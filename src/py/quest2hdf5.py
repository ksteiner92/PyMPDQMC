import sys
import os
import pandas as pd
import numpy as np
import math
from scipy import special
import scipy.integrate as integrate
from pandas import HDFStore,DataFrame
import optparse
import re

class QuestOutputParser:

    def parseTDMSpacialBlock(self, f, lineIdx, orb1, orb2, r, sym):
        cols = ["orb1", "orb2", "rx", "ry", "rz", "dist", "sym", "tau", "value", "error"]
        dist = math.sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2])
        dat = []
        for line in f[lineIdx:]:
            line = line.strip()
            lineIdx += 1
            if len(line) < 1:
                continue
            if len(line) < 4:
                raise Exception("Too less columns")
            if line[0] == '=':
                break
            tokens = line.split()
            dat.append([orb1, orb2, r[0], r[1], r[2], dist, sym, float(tokens[0]), float(tokens[1]), float(tokens[3])])

        return pd.DataFrame(data = dat, columns=cols), lineIdx

    def parseTDMFTBlock(self, f, lineIdx, orb1, orb2, kclass, kgrid, xcolname):
        cols = ["orb1", "orb2", "kclass", "kx", "ky", "kz", xcolname, "value", "error"]
        kpoints = kgrid[kclass]
        dat = []
        for line in f[lineIdx:]:
            line = line.strip()
            lineIdx += 1
            if len(line) < 1:
                continue
            if len(line) < 10:
                raise Exception("Too less columns")
            if line[0] == '=':
                break
            x = 0.0
            try:
                x = float(line[:line.index('(') - 1])
            except ValueError:
                continue
            rawValues = re.findall("\((.*?)\)", line)
            valParts = rawValues[0].strip().split('+-')
            valParts.extend(rawValues[1].strip().split('+-'))
            value = float(valParts[0]) + float(valParts[2]) * 1j
            error = float(valParts[1]) + float(valParts[3]) * 1j
            for kpoint in kpoints:
                dat.append([orb1, orb2, kclass, kpoint[0], kpoint[1], kpoint[2], x, value, error])
        return pd.DataFrame(data = dat, columns=cols), lineIdx

    def parse(self, outfilename):
        frames = {}
        with open(outfilename, "r") as f:
            print "parsing equal time measurements ..."
            idx = 0
            lines = f.readlines()
            while idx < len(lines):
                line = lines[idx].strip()
                if line in self.__spacialBlocks:
                    block = self.__spacialBlocks[line]
                    print " - parsing '" + block[0] + "' ..."
                    res = block[2](self, lines, idx + 1)
                    frames[block[1]] = res[0]
                    idx = res[1]
                elif line in self.__scalarBlocks:
                    block = self.__scalarBlocks[line]
                    print " - parsing '" + block[0] + "' ..."
                    res = block[1](self, lines, idx + 1)
                    frames[block[0]] = res[0]
                    idx = res[1]
                elif line in self.__kBlocks:
                    block = self.__kBlocks[line]
                    print " - parsing '" + block[0] + "' ..."
                    res = block[3](self, lines, idx + 1, self.__kgrids[block[1]])
                    frames[block[2]] = res[0]
                    idx = res[1]
                elif line in self.__kgridBlocks:
                    block = self.__kgridBlocks[line]
                    print " - parsing '" + block[0] + "' ..."
                    res = block[1](self, lines, idx + 1)
                    self.__kgrids[block[0]] = res[0]
                    idx = res[1]
                else:
                    idx += 1
        tdmOutputFile = os.path.splitext(outfilename)[0] + ".tdm.out"
        if frames and os.path.isfile(tdmOutputFile):
            with open(os.path.splitext(outfilename)[0] + ".tdm.out", "r") as f:
                print "parsing time dependent measurements ..."
                id = None
                idx = 0
                lines = f.readlines()
                res = {}
                while idx < len(lines):
                    line = lines[idx].strip()
                    idx += 1
                    if len(line) < 1:
                        continue
                    #Skip conductivity for now
                    if "Conductivity" in line:
                        l = line
                        while idx < len(lines) and (len(line) < 1 or l[0] != '='):
                            l = lines[idx].strip()
                            idx += 1
                        idx += 1
                        continue
                    else:
                        tokens = line.split()
                        df = None
                        if "k=" in tokens:
                            isSelfEn = "SelfEn" in line
                            if isSelfEn:
                                id = tokens[0]
                            else:
                                id = "FT" + tokens[0]
                            kclassOffset = tokens.index("k=")
                            for i in range(1, kclassOffset):
                                id += "_" + tokens[i]
                            id = id.replace("-", "")
                            kgrid = self.__kgrids[self.__tdmGridIDMapping[tokens[0]]]
                            kclass = int(tokens[kclassOffset + 1])
                            pairOffset = tokens.index("pair=")
                            orb1 = int(tokens[pairOffset + 1][0][:len(tokens[pairOffset + 1]) - 1])
                            orb2 = int(tokens[pairOffset + 2][0])
                            (df, idx) = self.parseTDMFTBlock(lines, idx, orb1, orb2, kclass, kgrid,\
                                                              "w_n" if isSelfEn else "tau")
                        else:
                            id = tokens[0]
                            orbOffset = 1
                            orb1 = 0
                            for i in range(1, len(tokens)):
                                try:
                                    orb1 = int(tokens[i])
                                    orbOffset = i
                                    break
                                except ValueError:
                                    id += "_" + tokens[i]
                            id = id.replace("-", "")
                            orb2 = int(tokens[orbOffset + 1])
                            r = [float(tokens[orbOffset + 2]), float(tokens[orbOffset + 3]), float(tokens[orbOffset + 4])]
                            sym = int(tokens[orbOffset + 5])
                            (df, idx) = self.parseTDMSpacialBlock(lines, idx, orb1, orb2, r, sym)
                        if not id in res:
                            res[id] = df
                        else:
                            res[id] = pd.concat([res[id], df])
                for k, v in res.iteritems():
                    frames["TDM/" + k] = v
        elif not frames:
            return ()
        return frames

    def parseScalarQuantities(self, f, lineIdx):
        cols = ["name", "value", "error", "type"]
        dat = []
        lineCount = 0
        for line in f[lineIdx:]:
            line = line.strip()
            lineCount += 1
            if len(line) < 1:
                continue
            if line[0] == '=':
                break
            tokens = line.split(':')
            if len(tokens) < 2:
                continue
            row = [None] * 4
            row[0] = tokens[0].strip()
            valtokens = tokens[1].split()
            values = []
            errors = []
            type = None
            parseValues = True
            for valtoken in valtokens:
                valtoken = valtoken.strip()
                if not valtoken:
                    break
                if valtoken == "+-":
                    parseValues = False
                    continue
                if parseValues:
                    try:
                        values.append(float(valtoken))
                        if not type:
                            type = "float"
                    except ValueError:
                        values.append(valtoken)
                        if not type:
                            type = "str"
                else:
                    errors.append(float(valtoken))
            if len(values) == 1:
                row[1] = values[0]
            elif len(values) > 1:
                row[1] = values
                type = "list"
            if len(errors) == 1:
                row[2] = errors[0]
            elif len(errors) > 1:
                row[2] = errors
            row[3] = type
            if row[1]:
                dat.append(row)
        df = pd.DataFrame(data = dat, columns=cols), (lineIdx + lineCount)
        return df

    def parseSparcialQuantity(self, f, lineIdx):
        cols = ["orb1", "orb2", "rx", "ry", "rz", "dist", "sym", "value", "error"]
        dat = []
        lineCount = 0
        for line in f[lineIdx:]:
            line = line.strip()
            lineCount += 1
            if len(line) < 1:
                continue
            if len(line) < 9:
                raise Exception("Too less columns")
            if line[0] == '=':
                break
            tokens = line.split()
            rx = float(tokens[2])
            ry = float(tokens[3])
            rz = float(tokens[4])
            dat.append([int(tokens[0]), int(tokens[1]), float(tokens[2]), float(tokens[3]), float(tokens[4]), \
                        math.sqrt(rx * rx + ry * ry + rz * rz), int(tokens[5]), float(tokens[6]), float(tokens[8])])
        return pd.DataFrame(data = dat, columns=cols), (lineIdx + lineCount)

    def parseKGrid(self, f, lineIdx):
        kgrid = {}
        currClass = 0
        lineCount = 0
        for line in f[lineIdx:]:
            line = line.strip()
            lineCount += 1
            if len(line) < 1:
                continue
            if line[0] == '=':
                break
            elif line == "K-points" or line == "Class":
                continue
            tokens = line.split()
            startIdx = 0
            if len(tokens) > 2:
                currClass = int(tokens[0])
                kgrid[currClass] = []
                startIdx = 1
            point = [0.0] * 3
            for i in range(startIdx, min(len(tokens), 3)):
                point[i] = float(tokens[i])
            kgrid[currClass].append(point)
        return kgrid, (lineIdx + lineCount)

    def parseFTQuantity(self, f, lineIdx, kgrid):
        cols = ["orb1", "orb2", "kclass", "kx", "ky", "kz", "value", "error"]
        dat = []
        kpoints = []
        kclass = 0
        lineCount = 0
        for line in f[lineIdx:]:
            line = line.strip()
            lineCount += 1
            if len(line) < 1:
                continue
            if line[0] == '=':
                break
            tokens = line.split()
            if len(tokens) < 5:
                raise Exception("too less columns")
            offset = 0
            if len(tokens) > 5:
                kclass = int(tokens[0])
                kpoints = kgrid[kclass]
                offset = 1
            for kpoint in kpoints:
                dat.append([int(tokens[offset]), int(tokens[offset + 1]), kclass, kpoint[0], kpoint[1], kpoint[2], \
                            float(tokens[offset + 2]), float(tokens[offset + 4])])
        return pd.DataFrame(data = dat, columns=cols), (lineIdx + lineCount)

    __kgrids = {}

    __tdmGridIDMapping = {
        "Gfun" : "Grid for Green's function",
        "SxSx": "Grid for spin/charge correlations",
        "SzSz": "Grid for spin/charge correlations",
        "Den-Den": "Grid for spin/charge correlations",
        "S-wave": "Grid for spin/charge correlations",
    }

    __spacialBlocks = {
        "Mean Equal time Green's function:": ("<G(r,r',0)>", "EQT/G", parseSparcialQuantity),
        "Up Equal time Green's function:": ("<G_up(r,r',0)>", "EQT/Gup", parseSparcialQuantity),
        "Down Equal time Green's function:": ("<G_dn(r,r',0)>", "EQT/Gdn", parseSparcialQuantity),
        "Density-density correlation fn: (up-up)": ("<n_up(r,0)n_up(r',0)>", "EQT/DupDup", parseSparcialQuantity),
        "Density-density correlation fn: (up-dn)": ("<n_up(r,0)n_dn(r',0)>", "EQT/DupDdn", parseSparcialQuantity),
        "XX Spin correlation function:": ("<S_x(r,0)S_x(r',0)>", "EQT/SxSx", parseSparcialQuantity),
        "ZZ Spin correlation function:": ("<S_z(r,0)S_z(r',0)>", "EQT/SzSz", parseSparcialQuantity),
        "Average Spin correlation function:": ("<S(r,0)S(r',0)>", "EQT/SS", parseSparcialQuantity),
        "Pairing correlation function:": ("<n_up(r,0)n_dn(r,0)n_up(r',0)n_dn(r',0)>", "EQT/P", parseSparcialQuantity)
    }

    __kBlocks = {
        "FT of Ave Equal t Green's function:": ("<G(k,k',0)>", "Grid for Green's function", "EQT/FTG", parseFTQuantity),
        "FT of Up Equal t Green's function:": ("<G_up(k,k',0)>", "Grid for Green's function", "EQT/FTGup", parseFTQuantity),
        "FT of Dn Equal t Green's function:": ("<G_dn(k,k',0)>", "Grid for Green's function", "EQT/FTGdn", parseFTQuantity),
        "FT of Density-density correlation fn: (up-up)": ("<n_up(k,0)n_up(k',0)>", "Grid for spin/charge correlations", "EQT/FTDupDup", parseFTQuantity),
        "FT of Density-density correlation fn: (up-dn)": ("<n_up(k,0)n_dn(k',0)>", "Grid for spin/charge correlations", "EQT/FTDupDdn", parseFTQuantity),
        "FT of XX spin correlation fn:": ("<S_x(k,0)S_x(k',0)>", "Grid for spin/charge correlations", "EQT/FTSxSx", parseFTQuantity),
        "FT of ZZ spin correlation fn:": ("<S_z(k,0)S_z(k',0)>", "Grid for spin/charge correlations", "EQT/FTSzSz", parseFTQuantity),
        "FT of Average spin correlation fn:": ("<S(k,0)S(k',0)>", "Grid for spin/charge correlations", "EQT/FTSS", parseFTQuantity),
        "FT of Pairing correlation fn:": ("<n_up(k,0)n_dn(k,0)n_up(k',0)n_dn(k',0)>", "Grid for spin/charge correlations", "EQT/FTP", parseFTQuantity)
    }

    __scalarBlocks = {
        "General Geometry - Free Format": ("Parameters", parseScalarQuantities),
        "Equal time measurements:": ("EQTM", parseScalarQuantities)
    }

    __kgridBlocks = {
        "Grid for Green's function": ("Grid for Green's function", parseKGrid),
        "Grid for spin/charge correlations": ("Grid for spin/charge correlations", parseKGrid)
    }

class Extractor:

    __projdir = os.getcwd()
    __N = 2000
    __L = 100
    __matsubara = False

    def setProjectDir(self, projdir):
        self.__projdir = os.path.abspath(projdir)

    def setNumLegendre(self, L):
        self.__L = L

    def setNumFrequencies(self, N):
        self.__N = N

    def calcMatsubara(self, matsubara):
        self.__matsubara = matsubara

    def calcGiw(self, frame):
        G_tau = frame['TDM/Gfun']
        b = float(frame['PARAM/Float'].query("name=='beta'").value.values[0])
        rGroups = G_tau.groupby(["rx", "ry", "rz"])
        allR = [r for r, v in rGroups.groups.items()]
        for r in allR:
            print "Calculate Giw for r=(" + str(r[0]) + "," + str(r[1]) + "," + str(r[2]) + ") ..."
            G_tau_0 = G_tau.query("rx==" + str(r[0]) + " and ry==" + str(r[1]) + " and rz==" + str(r[2])) \
                .groupby("tau", as_index=False).mean() \
                .sort_values(by="tau")
            last = G_tau_0.query("tau==0")
            last.tau = b
            G_tau_0 = G_tau_0.append(last, ignore_index=True)
            G_tau_0.value = G_tau_0.value.apply(lambda x: -x)
            P_l = np.polynomial.legendre.legfit(G_tau_0.tau, G_tau_0.value, self.__L - 1)
            G = np.polynomial.legendre.Legendre(P_l)
            Gl = np.ndarray(shape=(self.__L), dtype=float)
            Gerror = np.ndarray(shape=(self.__L), dtype=float)
            for l in range(0, self.__L):
                I = integrate.quad(lambda tau: special.eval_legendre(l, 2.0 * tau / float(b) - 1.0) * G(tau), \
                                   0.0, float(b))
                Gl[l] = np.sqrt(2.0 * l + 1.0) * I[0]
                Gerror[l] = I[1]
            N = self.__N + 1
            T_nl = np.ndarray(shape=(N, self.__L), dtype=complex)
            for n in range(0, N):
                for l in range(0, self.__L):
                    T_nl[n][l] = (-1)**n * 1.0j**(l + 1) * (2.0 * l + 1)**(0.5) * \
                                 special.spherical_jn(l, (2.0 * n + 1.0) * np.pi * 0.5)
            Giw = T_nl.dot(Gl)
            df = pd.DataFrame({"w_n": [np.pi / float(b) * (2 * n + 1.) for n in range(0, N)], \
                               "orb1": np.full(N, G_tau_0.orb1.values[0]),\
                               "orb2": np.full(N, G_tau_0.orb2.values[0]),\
                               "rx": np.full(N, r[0]),\
                               "ry": np.full(N, r[1]),\
                               "rz": np.full(N, r[2]),\
                               "dist": np.full(N, G_tau_0.dist.values[0]),\
                               "value": [-np.real(g) + 1.0j*np.imag(g) for g in Giw],\
                               "error" : np.full(N, 0.0)})
            if not "TDM/Giw" in frame:
                frame["TDM/Giw"] = df
            else:
                frame["TDM/Giw"] = pd.concat([frame["TDM/Giw"], df])
        return frame

    def extract(self, keys):
        frames = None
        for root, dirs, files in  os.walk(self.__projdir):
            for f in files:
                fnameparts = os.path.splitext(f)
                if fnameparts[1] == ".out" and not os.path.splitext(fnameparts[0])[1] == ".tdm":
                    print "Parsing simulation '" + str(f) + "' ..."
                    parser = QuestOutputParser()
                    simFrames = parser.parse(os.path.realpath(os.path.join(root, f)))
                    if not simFrames:
                        continue
                    simParams = simFrames["Parameters"]
                    floatParams = simParams.query("type == 'float'")
                    floatParams = floatParams.drop(['type'], axis=1)
                    floatParams.value = floatParams.value.apply(lambda x: float(x))
                    simFrames["PARAM/Float"] = floatParams
                    listParams = simParams.query("type == 'list'")
                    listParams = listParams.drop(['type'], axis=1)
                    listParams.value = listParams.as_matrix(columns=['value'])
                    #simFrames["PARAM/List"] = listParams
                    strParams = simParams.query("type == 'str'")
                    strParams = strParams.drop(['type'], axis=1)
                    simFrames["PARAM/String"] = strParams
                    if self.__matsubara:
                        simFrames = self.calcGiw(simFrames)
                    keyValues = []
                    for key in keys:
                        row = simParams[simParams.name == key]
                        type = str(row.type.values[0])
                        if type == "float":
                            keyValues.append(float(row.value.values[0]))
                        elif type == "list":
                            keyValues.append(float(row.value.values[0][0]))
                    initFrames = not frames
                    if initFrames:
                        frames = {}
                    for k, frame in simFrames.iteritems():
                        for key, keyValue in zip(keys, keyValues):
                            frame[str(key)] = keyValue
                        if initFrames:
                            frames[k] = frame
                        else:
                            frames[k] = pd.concat([frames[k], frame])
        return frames

parser = optparse.OptionParser(usage="%prog [keys] [options]")
parser.add_option("--output", "-o", type="string", metavar="FILE", dest="output", help="The name of the output file")
parser.add_option("--proj-dir", "-p", type="string", metavar="DIR", dest="projdir",\
                  help="The root directory from which %prog should start looking recursively")
matsubaraGroup = optparse.OptionGroup(parser, "Matsubara Options")
matsubaraGroup.add_option("--matsubara", "-m", action="store_true", dest="matsubara", help="")
matsubaraGroup.add_option("--l-max", "-l", type="int", dest="lmax", metavar="NUM", default=100, help="")
matsubaraGroup.add_option("--n-frequencies", "-n", type="int", dest="nfreq", metavar="NUM", default=2000, help="")
parser.add_option_group(matsubaraGroup)

(options, args) = parser.parse_args()

ext = Extractor()
ext.calcMatsubara(options.matsubara)
ext.setNumFrequencies(options.nfreq)
ext.setNumLegendre(options.lmax)
if options.projdir:
    ext.setProjectDir(os.path.abspath(options.projdir))
frames = ext.extract(args)
hdf = HDFStore(options.output if options.output  else "output.hdf5")
for k, frame in frames.iteritems():
    if k != "Parameters":
        hdf.put(k, frame, format='table', data_columns=True, index=False)
hdf.close()
print "Extraction complete."