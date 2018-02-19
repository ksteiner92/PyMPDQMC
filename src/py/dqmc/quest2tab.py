import sys
import os
import pandas as pd
import math
from pandas import HDFStore,DataFrame

class QuestOutputParser:

    def parseTDMSpacialBlock(self, f, lineIdx):
        print ""

    def parseTDMFTBlock(self, f, lineIdx):
        cols = ["orb1", "orb2", "kclass", "kx", "ky", "kz", "tau", "value", "error"]
        tokens = f[lineIdx].strip().split()
        lineIdx += 1
        id = tokens[0]
        kdtm = True
        kclassOffset = tokens.index("k=")
        for i in range(1, kclassOffset):
            id += "_" + tokens[i]
        kgrid = self.__kgrids[self.__tdmGridIDMapping[tokens[0]]]
        kclass = int(tokens[kclassOffset + 1])
        kpoints = kgrid[kclass]
        pairOffset = tokens.index("pair=")
        #TODO fetch index of ,
        orb1 = int(tokens[pairOffset + 1][0])
        orb2 = int(tokens[pairOffset + 2][0])
        dat = []
        for line in f[lineIdx:]:
            line = f[lineIdx].strip()
            lineIdx += 1
            if len(line) < 1:
                continue
            if len(line) < 9:
                raise Exception("Too less columns")
            if line[0] == '=':
                break
            tokens = line.split()
            tau = float(tokens[0])
            value = float(tokens[2]) + float(tokens[6])
            for kpoint in kpoints:
                dat.apppend([orb1, orb2, kclass, kpoint[0], kpoint[1], kpoint[2], tau, ])
        df = None
        for kpoint in kpoints:
            dfSub = dfRaw.copy()
            dfSub = dfSub.insert(0, "kz", kpoint[2])
            dfSub = dfSub.insert(0, "ky", kpoint[1])
            dfSub = dfSub.insert(0, "kx", kpoint[0])
            dfSub = dfSub.insert(0, "kclass", kclass)
            dfSub = dfSub.insert(0, "orb2", orb1)
            dfSub = dfSub.insert(0, "orb1", orb1)
            if not df:
                df = dfSub
            else:
                df = pd.concat([dfSub, df])

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
                kdtm = False
                res = {}
                for line in lines:
                    tokens = line.strip().split()
                    idx += 1
                    if not id:
                        if "k=" in tokens or kdtm:
                            id = tokens[0]
                            kdtm = True
                            kclassOffset = tokens.index("k=")
                            for i in range(1, kclassOffset):
                                id += "_" + tokens[i]
                            preCols = []
                            kgrid = self.__kgrids[self.__tdmGridIDMapping[tokens[0]]]
                            kclass = int(tokens[kclassOffset + 1])
                            kpoints = kgrid[kclass]
                            pairOffset = tokens.index("pair=")
                            orb1 = int(tokens[pairOffset + 1][0])
                            orb2 = int(tokens[pairOffset + 2][0])
                            (dfRaw, idx) = parseTDMFTBlock(lines, idx)
                            df = None
                            for kpoint in kpoints:
                                dfSub = dfRaw.copy()
                                dfSub = dfSub.insert(0, "kz", kpoint[2])
                                dfSub = dfSub.insert(0, "ky", kpoint[1])
                                dfSub = dfSub.insert(0, "kx", kpoint[0])
                                dfSub = dfSub.insert(0, "kclass", kclass)
                                dfSub = dfSub.insert(0, "orb2", orb1)
                                dfSub = dfSub.insert(0, "orb1", orb1)
                                if not df:
                                    df = dfSub
                                else:
                                    df = pd.concat([dfSub, df])
                            res[id]
                        else:



            return frames
        else:
            return ()

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
        "Mean Equal time Green's function:": ("<G(r,r',0)>", "MEQTG", parseSparcialQuantity),
        "Up Equal time Green's function:": ("<G_up(r,r',0)>", "MEQTGup", parseSparcialQuantity),
        "Down Equal time Green's function:": ("<G_dn(r,r',0)>", "MEQTGdn", parseSparcialQuantity),
        "Density-density correlation fn: (up-up)": ("<n_up(r,0)n_up(r',0)>", "MEQTDupDup", parseSparcialQuantity),
        "Density-density correlation fn: (up-dn)": ("<n_up(r,0)n_dn(r',0)>", "MEQTDupDdn", parseSparcialQuantity),
        "XX Spin correlation function:": ("<S_x(r,0)S_x(r',0)>", "MEQTSxSx", parseSparcialQuantity),
        "ZZ Spin correlation function:": ("<S_z(r,0)S_z(r',0)>", "MEQTSzSz", parseSparcialQuantity),
        "Average Spin correlation function:": ("<S(r,0)S(r',0)>", "MEQTSS", parseSparcialQuantity),
        "Pairing correlation function:": ("<n_up(r,0)n_dn(r,0)n_up(r',0)n_dn(r',0)>", "MEQTP", parseSparcialQuantity)
    }

    __kBlocks = {
        "FT of Ave Equal t Green's function:": ("<G(k,k',0)>", "Grid for Green's function", "FTMEQTG", parseFTQuantity),
        "FT of Up Equal t Green's function:": ("<G_up(k,k',0)>", "Grid for Green's function", "FTMEQTGup", parseFTQuantity),
        "FT of Dn Equal t Green's function:": ("<G_dn(k,k',0)>", "Grid for Green's function", "FTMEQTGdn", parseFTQuantity),
        "FT of Density-density correlation fn: (up-up)": ("<n_up(k,0)n_up(k',0)>", "Grid for spin/charge correlations", "FTMEQTDupDup", parseFTQuantity),
        "FT of Density-density correlation fn: (up-dn)": ("<n_up(k,0)n_dn(k',0)>", "Grid for spin/charge correlations", "FTMEQTDupDdn", parseFTQuantity),
        "FT of XX spin correlation fn:": ("<S_x(k,0)S_x(k',0)>", "Grid for spin/charge correlations", "FTMEQTSxSx", parseFTQuantity),
        "FT of ZZ spin correlation fn:": ("<S_z(k,0)S_z(k',0)>", "Grid for spin/charge correlations", "FTMEQTSzSz", parseFTQuantity),
        "FT of Average spin correlation fn:": ("<S(k,0)S(k',0)>", "Grid for spin/charge correlations", "FTMEQTSS", parseFTQuantity),
        "FT of Pairing correlation fn:": ("<n_up(k,0)n_dn(k,0)n_up(k',0)n_dn(k',0)>", "Grid for spin/charge correlations", "FTMEQTP", parseFTQuantity)
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

    def setProjectDir(self, projdir):
        self.__projdir = os.path.abspath(projdir)

    def extract(self, *keys):
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
                    keyValues = []
                    for key in keys:
                        row = simParams[simParams.name == key]
                        type = str(row.type).split()[1]
                        if type == "float":
                            keyValues.append(float(row.value))
                        elif type == "list":
                            keyValues.append(float(row.value[0][0]))
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

ext = Extractor()
#ext.setProjectDir("/home/klsteine/kagome/dqmc/res/5x5.2")
frames = ext.extract("beta", "U")
hdf = HDFStore("kagome.5x5.hdf5")
for k, frame in frames.iteritems():
    if k != "Parameters":
        hdf.put(k, frame, format='table', data_columns=True)
print hdf
hdf.close()