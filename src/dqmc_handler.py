import dqmc

"""
Wrapper functions
"""
class DQMCHandler:

    def __init__(self, finput):
        if not dqmc.ggeom_init(finput):
            raise Exception("Could not initialize dqmc module")

    def __exit__(self, exc_type, exc_value, traceback):
        dqmc.ggeom_close()

    def run(self):
        dqmc.ggeom_run()

    def calculateDensity(self, mu):
        return dqmc.ggeom_calculatedensity(mu)

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

    def setBeta(self, beta, dtaumax):
        L = int(beta / dtaumax)
        if (L < 10):
            L = 10
            dqmc.ggeom_setparameteri("north", 5)
        elif (abs(float(L) - (beta / dtaumax)) > 1e-4):
            L = L + 1
        north = dqmc.ggeom_getparameteri("north")
        dtau = beta / float(L)
        dqmc.ggeom_setparameterr("dtau", dtau)
        dqmc.ggeom_setparameteri("L", L)

    def setChemicalPotential(self, mu):
        dqmc.ggeom_setuniformmu(mu)