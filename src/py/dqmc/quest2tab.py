import sys
import os
from pandas import DataFrame
import pandas as pd

class QuestOutputParser:

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
                    res = block[1](self, lines, idx + 1)
                    frames[block[0]] = res[0]
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
                    res = block[2](self, lines, idx + 1, self.__kgrids[block[1]])
                    frames[block[0]] = res[0]
                    idx = res[1]
                elif line in self.__kgridBlocks:
                    block = self.__kgridBlocks[line]
                    print " - parsing '" + block[0] + "' ..."
                    res = block[1](self, lines, idx + 1)
                    self.__kgrids[block[0]] = res[0]
                    idx = res[1]
                else:
                    idx += 1
        with open(os.path.splitext(outfilename)[0] + ".tdm.out", "r") as f:
            print "parsing time dependent measurements ..."

        return frames

    def parseScalarQuantities(self, f, lineIdx):
        cols = ["name", "value", "error"]
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
            row = [None] * 3
            row[0] = tokens[0].strip()
            valtokens = tokens[1].split()
            values = []
            errors = []
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
                    except ValueError:
                        values.append(valtoken)
                else:
                    errors.append(float(valtoken))
            if len(values) == 1:
                row[1] = values[0]
            elif len(values) > 1:
                row[1] = values
            if len(errors) == 1:
                row[2] = errors[0]
            elif len(errors) > 1:
                row[2] = errors
            if row[1]:
                dat.append(row)
        return pd.DataFrame(data = dat, columns=cols), (lineIdx + lineCount)

    def parseSparcialQuantity(self, f, lineIdx):
        cols = ["orb1", "orb2", "rx", "ry", "rz", "sym", "value", "error"]
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
            dat.append([int(tokens[0]), int(tokens[1]), float(tokens[2]), float(tokens[3]), float(tokens[4]), \
                        int(tokens[5]), float(tokens[6]), float(tokens[8])])
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

    __spacialBlocks = {
        "Mean Equal time Green's function:": ("<G(r,r',0)>", parseSparcialQuantity),
        "Up Equal time Green's function:": ("<G_up(r,r',0)>", parseSparcialQuantity),
        "Down Equal time Green's function:": ("<G_dn(r,r',0)>", parseSparcialQuantity),
        "Density-density correlation fn: (up-up)": ("<n_up(r,0)n_up(r',0)>", parseSparcialQuantity),
        "Density-density correlation fn: (up-dn)": ("<n_up(r,0)n_dn(r',0)>", parseSparcialQuantity),
        "XX Spin correlation function:": ("<S_x(r,0)S_x(r',0)>", parseSparcialQuantity),
        "ZZ Spin correlation function:": ("<S_z(r,0)S_z(r',0)>", parseSparcialQuantity),
        "Average Spin correlation function:": ("<S(r,0)S(r',0)>", parseSparcialQuantity),
        "Pairing correlation function:": ("<n_up(r,0)n_dn(r,0)n_up(r',0)n_dn(r',0)>", parseSparcialQuantity)
    }

    __kBlocks = {
        "FT of Ave Equal t Green's function:": ("<G(k,k',0)>", "Grid for Green's function", parseFTQuantity),
        "FT of Up Equal t Green's function:": ("<G_up(k,k',0)>", "Grid for Green's function", parseFTQuantity),
        "FT of Dn Equal t Green's function:": ("<G_dn(k,k',0)>", "Grid for Green's function", parseFTQuantity),
        "FT of Density-density correlation fn: (up-up)": ("<n_up(k,0)n_up(k',0)>", "Grid for spin/charge correlations", parseFTQuantity),
        "FT of Density-density correlation fn: (up-dn)": ("<n_up(k,0)n_dn(k',0)>", "Grid for spin/charge correlations", parseFTQuantity),
        "FT of XX spin correlation fn:": ("<S_x(k,0)S_x(k',0)>", "Grid for spin/charge correlations", parseFTQuantity),
        "FT of ZZ spin correlation fn:": ("<S_z(k,0)S_z(k',0)>", "Grid for spin/charge correlations", parseFTQuantity),
        "FT of Average spin correlation fn:": ("<S(k,0)S(k',0)>", "Grid for spin/charge correlations", parseFTQuantity),
        "FT of Pairing correlation fn:": ("<n_up(k,0)n_dn(k,0)n_up(k',0)n_dn(k',0)>", "Grid for spin/charge correlations", parseFTQuantity)
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

    def extract(self, *args):
        frames = []
        for root, dirs, files in  os.walk(self.__projdir):
            for f in files:
                fnameparts = os.path.splitext(f)
                if fnameparts[1] == ".out" and not os.path.splitext(fnameparts[0])[1] == ".tdm":
                    print "Parsing simulation '" + str(f) + "' ..."
                    parser = QuestOutputParser()
                    simFrames = parser.parse(os.path.realpath(os.path.join(root, f)))
                    simParams = simFrames["Parameters"]
                    beta =  float(simParams[simParams.name == "beta"].value)
                    U = float(simParams[simParams.name == "U"].value[0][0])
                    print beta, U
                    frames.append(simFrames)
                    break

        #return (pd.DataFrame(data = res, columns=cols), pd.DataFrame(data = spacial), pd.DataFrame(data = tdm))

ext = Extractor()
ext.extract("beta", "U")