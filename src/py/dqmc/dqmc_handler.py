import dqmc

class DQMCHandler:

    __minLFactor = 2

    def __init__(self, finput):
        if not dqmc.ggeom_init(finput):
            raise Exception("Could not initialize dqmc module")

    def __exit__(self, exc_type, exc_value, traceback):
        dqmc.ggeom_close()

    def run(self):
        dqmc.ggeom_run()

    def calculateDensity(self, mu):
        return  dqmc.ggeom_calculatedensity(mu)

    def writeConfig(self, fname):
         dqmc.ggeom_writeconfig(fname)

    def setParameter(self, name, value, t):
        if (t == "float"):
            dqmc.ggeom_setparameterr(name, float(value))
        elif (t == "int"):
            dqmc.ggeom_setparameteri(name, int(value))
        elif (t == "str"):
            dqmc.ggeom_setparameters(name, str(value))
        elif (t == "pfloat"):
            n = len(value)
            val = [0.0] * n
            for i in range(0, n):
                val[i] = float(value[i])
            dqmc.ggeom_setparameterpr(name, n, val)
        elif (t == "pint"):
            n = len(value)
            val = [0] * n
            for i in range(0, n):
                val[i] = int(value[i])
            dqmc.ggeom_setparameterpi(name, n, val)
        else:
            raise Exception("setParameter: type '", t, "' not supported")

    def getParameter(self, name, t):
        if (t == "float"):
            return dqmc.ggeom_getparameterr(name)
        elif (t == "int"):
            return dqmc.ggeom_getparameteri(name)
        elif (t == "str"):
            value = ""
            dqmc.ggeom_getparameters(name, value)
            return value
        else:
            raise Exception("getParameter: type '" + t + "' not supported")

    def setGeomFile(self, gfile):
        dqmc.ggeom_setgeomfile(gfile)

    def setNumThreads(self, nthreads):
        dqmc.ggeom_setnumthreads(nthreads)

    def setMinLFactor(self, minLFactor):
        self.__minLFactor = minLFactor

    def setBeta(self, beta, dtaumax):
        north = dqmc.ggeom_getparameteri("north")
        L = int(beta / dtaumax)
        if (L < self.__minLFactor * north):
            L = self.__minLFactor * north
        elif (L % north) != 0:
            L = (int(L) / int(north)) * north + north
        dtau = beta / float(L)
        dqmc.ggeom_setparameterr("dtau", dtau)
        dqmc.ggeom_setparameteri("L", L)

    def setChemicalPotential(self, mu):
        dqmc.ggeom_setuniformmu(mu)