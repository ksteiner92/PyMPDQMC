import os
import sys
import dqmc
from pathos.multiprocessing import Pool
import time
import optparse
import signal
import yaml
import numpy as np

"""
Wrapper function
"""
def calculateDensity(mu):
    return dqmc.ggeom_calculatedensity(mu)

def run():
    dqmc.ggeom_run()

class MPDQMC:
    __pool = None

    def __init__(self, finput, ncpus):
        print "Initializing process pool ..."
        if not dqmc.ggeom_init(finput):
            raise Exception("Could not initialize dqmc module")
        self.__pool = Pool(processes = ncpus)

    def __exit__(self, exc_type, exc_value, traceback):
        dqmc.ggeom_close()

    def calcPotentialForDensity(self, mu1, mu2, rho, maxit, epsilon = 1e-10):
        print "Starting regular falsi ..."

        print "Starting process for mu = ", mu1, " ..."
        fso = self.__pool.apply_async(calculateDensity, (mu1,))
        print "Starting process for mu = ", mu2, " ..."
        fto = self.__pool.apply_async(calculateDensity, (mu2,))
        #self.__pool.close()
        print "Waiting ... "
        #try:
        #    self.__pool.join()
        #except KeyboardInterrupt:
        #    print "KeyboardInterrupt => terminating pool ..."
        #    self.__pool.terminate()
        fs = fso.get()
        ft = fto.get()

        print "rho = ", fs, " for mu = ", mu1
        print "rho = ", ft, " for mu = ", mu2

        mu = 0.0
        for i in range(1, maxit):
            mu = (rho - ft) * (mu2 - mu1) / (ft - fs) + mu2
            print "new mu = ", mu
            fro = self.__pool.apply_async(calculateDensity, (mu,))
            fr = fro.get()
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

    def setParameter(self, name, value):
        t = type(value)
        if (t == float):
            dqmc.ggeom_setparameterr(name, value)
        elif (t == int):
            dqmc.ggeom_setparameteri(name, value)
        elif (t == str):
            dqmc.ggeom_setparameters(name, value)
        else:
            raise Exception("setParameter: type not supported")

    def getParameter(self, name, value):
        t = type(value)
        if (t == float):
            return dqmc.ggeom_getparameterr(name)
        elif (t == int):
            return dqmc.ggeom_getparameteri(name)
        elif (t == str):
            dqmc.ggeom_getparameters(name, value)
        else:
            raise Exception("getParameter: type not supported")
        return value

if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog [OPTIONS] <input>")
    parser.add_option("--num-cpus", type = "int", metavar = "CPUS", dest = "ncpus", default = 1,
                      help = "Number of cpus which should be used")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        sys.exit("Not enough arguments given")

    mpdqmc = MPDQMC(args[0], options.ncpus)
    mpdqmc.setParameter("dtau", 0.1)
    val = 0.0
    print "dtau: ", mpdqmc.getParameter("dtau", val)
    #mu = mpdqmc.calcPotentialForDensity(-1, 1, 1, 10, 1e-6)