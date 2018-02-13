import sys
import os

class Extractor:

    class Data:
        value = 0.0
        error = None

    __tolerance = 1.0e-4
    __projdir = os.getcwd()

    def setProjectDir(self, projdir):
        self.__projdir = os.path.abspath(projdir)

    def extract(self, *args):
        keys = args[0]
        constraints = {}
        if len(args) > 1:
            constraints = args[1]
        print constraints
        res = {}
        spacialdep = False
        for root, dirs, files in  os.walk(self.__projdir):
            for f in files:
                fnameparts = os.path.splitext(f)
                if fnameparts[1] == ".out" and not os.path.splitext(fnameparts[0])[1] == ".tdm":
                    values = []
                    firstline = True
                    key = None
                    with open(os.path.realpath(os.path.join(root, f)), "r") as out:
                        for line in out:
                            if firstline:
                                if not line.strip().startswith("General Geometry - Free Format"):
                                    break
                                firstline = False
                            if not spacialdep:
                                pair = line.split(':')
                                quan = pair[0].strip()
                                if quan in keys:
                                    valcol = pair[1].strip()
                                    if len(pair) > 1 and valcol:
                                        valpair = valcol.split("+-")
                                        idx = keys.index(quan)
                                        dat = Extractor.Data()
                                        dat.value = float(valpair[0].strip())
                                        if len(valpair) > 1 and valpair[1].strip():
                                            dat.error = float(valpair[1].strip())
                                        if idx == 0:
                                            key = dat
                                        else:
                                            values.append(dat)
                                    else:
                                        spacialdep = True
                            else:
                                tokens = line.split()
                                if tokens[0][0] == "=":
                                    spacialdep = False
                                    break
                                match = True
                                if (match and ("orb1" in constraints) and constraints["orb1"]):
                                    match = int(constraints["orb1"]) == int(tokens[0])
                                if (match and ("orb2" in constraints) and constraints["orb2"]):
                                    match = int(constraints["orb2"]) == int(tokens[1])
                                if (match and ("x" in constraints) and constraints["x"]):
                                    match = (float(constraints["x"]) - float(tokens[2])) < self.__tolerance
                                if (match and ("y" in constraints) and constraints["y"]):
                                    match = (float(constraints["y"]) - float(tokens[3])) < self.__tolerance
                                if (match and ("z" in constraints) and constraints["z"]):
                                    match = (float(constraints["z"]) - float(tokens[4])) < self.__tolerance
                                if match:
                                    dat = Extractor.Data()
                                    dat.value = float(tokens[6])
                                    dat.error = float(tokens[8])
                                    values.append(dat)
                    if key:
                        res[key] = values

        return [(key, value) for key, value in sorted(res.iteritems())]
