import os
import sys
from dqmc import dqmc_handler
import optparse
import ast
import numpy

def setParam(dqmchandle, name, v):
    t = v["type"]
    val = v["value"]
    dqmchandle.setParameter(name, val, t)

"""
    Input:
        beta*: float
        dtaumax*: float
        mu: float
        calcmu: 
            rho*: float
            mu_start*: float
            mu_end*: float
            maxit: int
            epsilon: float
        params:
            [
                ...:
                    type*: str
                    value*: str
            ]
"""
if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog <input>")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        sys.exit("Not enough arguments given")

    input = ast.literal_eval(args[0])
    dqmchandle = dqmc_handler.DQMCHandler(str(input["input"]))

    if ("mu" in input):
        dqmchandle.setChemicalPotential(float(input["mu"]))

    dtaumax = input["dtaumax"]
    beta = input["beta"]
    dqmchandle.setBeta(beta, dtaumax)

    #if ("U" in input):
    #    dqmchandle.setU(float(input["U"]))

    if ("params" in input):
        params = input["params"]
        for name, v in params.items():
            setParam(dqmchandle, name, v)

    if ("gfile" in input):
        gfile = input["gfile"]
        dqmchandle.setGeomFile(gfile)

    if ("calcmu" in input):
        calcmu = input["calcmu"]
        rho = calcmu["rho"]
        mu_start = calcmu["mu_start"]
        mu_end = calcmu["mu_end"]
        maxit = 10
        if "maxit" in calcmu: maxit = calcmu["maxit"]
        epsilon = 1e-6
        if "epsilon" in calcmu: calcmu["epsilon"]
        if ("params" in input):
            params = calcmu["params"]
            for name, v in params.items():
                setParam(dqmchandle, name, v)
        print "Find chemical potential for rho = ", rho, " ..."
        mu = dqmchandle.calcPotentialForDensity(mu_start, mu_end, rho, maxit, epsilon)
        print "Found chemical potential for rho = ", rho, " to be ", mu
    print "Start dqmc ..."
    dqmchandle.run()