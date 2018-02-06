#!/home/ksteiner/opt/bin/python
import os
import sys
from dqmc import dqmc_handler
import optparse
import ast
import numpy
import subprocess

def setParam(dqmchandle, name, v):
    t = v["type"]
    val = v["value"]
    dqmchandle.setParameter(name, val, t)


def calcPotentialForDensity(dqmchandle, mu1, mu2, rho, maxit, epsilon = 1e-10):
    print "Starting regular falsi ..."
    #log = open()
    print "Calculate start mu = ", mu1, " ..."
    sys.stdout.flush()
    fs = dqmchandle.calculateDensity(float(mu1))
    print "Start rho = ", fs
    print "Calculate end mu = ", mu2, " ..."
    sys.stdout.flush()
    ft = dqmchandle.calculateDensity(float(mu2))
    print "End rho = ", ft
    sys.stdout.flush()

    mu = 0.0
    for i in range(1, maxit):
        mu = (rho - ft) * (mu2 - mu1) / (ft - fs) + mu2
        print "new mu = ", mu
        sys.stdout.flush()
        fr = dqmchandle.calculateDensity(float(mu))
        print "rho = ", fr
        sys.stdout.flush()
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

    #check if ${prefix}.in exists, if so, preprocessing has
    # been done already
    #######################################################
    prefix = input["prefix"]
    cfgfile = prefix + ".in"
    preprocess = not os.path.isfile(os.path.abspath(cfgfile))
    if preprocess:
        cfgfile = input["input"]

    #initialize dqmc
    ################
    dqmchandle = dqmc_handler.DQMCHandler(cfgfile)

    #set chemical potential if given
    ################################
    if ("mu" in input):
        dqmchandle.setChemicalPotential(float(input["mu"]))

    #set temperature
    ################
    dtaumax = input["dtaumax"]
    beta = input["beta"]
    dqmchandle.setBeta(beta, dtaumax)

    #set additional parameters if given
    ###################################
    if ("params" in input):
        params = input["params"]
        for name, v in params.items():
            setParam(dqmchandle, name, v)

    #set geometry file if given
    ###########################
    if ("gfile" in input):
        gfile = input["gfile"]
        dqmchandle.setGeomFile(gfile)

    #if there is not ${prefix}.in file given we assume we have to do
    # preprocessing
    ##################################################################
    if preprocess:
        restoreparams = {}
        if "calcmu" in input:
            calcmu = input["calcmu"]
            rho = calcmu["rho"]
            mu_start = calcmu["mu_start"]
            mu_end = calcmu["mu_end"]
            maxit = 10
            if "maxit" in calcmu: maxit = calcmu["maxit"]
            epsilon = 1e-6
            if "epsilon" in calcmu: calcmu["epsilon"]
            #set additonal parameters for calcmu preprocessing
            if ("params" in calcmu):
                params = calcmu["params"]
                for name, v in params.items():
                    restorep = {}
                    restorep["value"] = str(dqmchandle.getParameter(name, v["type"]))
                    restorep["type"] = v["type"]
                    restoreparams[name] = restorep
                    setParam(dqmchandle, name, v)
            print "Find chemical potential for rho = ", rho, " ..."
            sys.stdout.flush()
            mu = calcPotentialForDensity(dqmchandle, mu_start, mu_end, rho, maxit, epsilon)
            print "Found chemical potential for rho = ", rho, " to be ", mu
            sys.stdout.flush()

        #restore parameters which have be changed during any preprocessing
        if restoreparams:
            print "Restoring parameters for simulation ..."
            sys.stdout.flush()
            for name, v in restoreparams.items():
                print " - restoring '", name, ", = ", v["value"]
                sys.stdout.flush()
                setParam(dqmchandle, name, v)
        #save configuration in ${prefix}.in
        cfgfile = prefix + ".in"
        dqmchandle.writeConfig(cfgfile)

    print "Start dqmc ..."
    sys.stdout.flush()
    dqmchandle.run()
