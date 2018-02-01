import dqmc

"""
Wrapper functions
"""
def calculateDensity(mu):
    return dqmc.ggeom_calculatedensity(mu)

def run():
    dqmc.ggeom_run()

class DQMCHandler:

    def __init__(self, finput):
        if not dqmc.ggeom_init(finput):
            raise Exception("Could not initialize dqmc module")

    def __exit__(self, exc_type, exc_value, traceback):
        dqmc.ggeom_close()

    def calcPotentialForDensity(self, mu1, mu2, rho, maxit, epsilon = 1e-10):
        print "Starting regular falsi ..."
        print "Calculate start mu = ", mu1, " ..."
        fs = calculateDensity(mu1)
        print "Start rho = ", fs
        print "Calculate end mu = ", mu2, " ..."
        ft = calculateDensity(mu2)
        print "End rho = ", ft

        mu = 0.0
        for i in range(1, maxit):
            mu = (rho - ft) * (mu2 - mu1) / (ft - fs) + mu2
            print "new mu = ", mu
            fr = calculateDensity(mu)
            print "rho = ", fr
            if (abs(fr - rho) < epsilon):
                return mu
            if ((fr - rho) * (ft - rho) > 0):
                mu2 = mu
                ft = fr
            elif ((fs - rho) * (fr - rho) > 0):
                mu1 = mu
                fs = fr
            else:
                return mu
        return mu

    def run(self):
        run()

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
        if (t == float):
            return dqmc.ggeom_getparameterr(name)
        elif (t == int):
            return dqmc.ggeom_getparameteri(name)
        elif (t == str):
            value = ""
            dqmc.ggeom_getparameters(name, value)
            return value
        else:
            raise Exception("getParameter: type not supported")

    def setGeomFile(self, gfile):
        dqmc.ggeom_setgeomfile(gfile)

    def setBeta(self, beta, dtaumax):
        L = int(beta / dtaumax)
        if (abs(float(L) - (beta / dtaumax)) > 1e-4):
            L = L + 1
        elif (L == 0):
            L = 10
            #dqmc.ggeom_setparameteri("north", 5)

        dtau = beta / float(L)
        dqmc.ggeom_setparameterr("dtau", dtau)
        dqmc.ggeom_setparameteri("L", L)

    def setUpChemicalPotential(self, mu):
        dqmc.ggeom_setuniformmu_up(mu)

    def setDnChemicalPotential(self, mu):
        dqmc.ggeom_setuniformmu_dn(mu)

    #def setU(self, U):
    #    dqmc.ggeom_setuniformU(U)