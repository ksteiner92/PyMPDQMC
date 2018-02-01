import os
import sys
import optparse
import ast

if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog <input>")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        sys.exit("Not enough arguments given")

    input = ast.literal_eval(args[0])
    mpdqmc = MPDQMC(str(input["input"]), int(input["np"]))
    params = input["params"]
    dtaumax = params["dtaumax"]

    for beta in params["beta"]:
        mpdqmc.setBeta(beta, dtaumax)


    #mpdqmc.setParameter("dtau", 0.1)
    #val = 0.0
    #print "dtau: ", mpdqmc.getParameter("dtau", val)
    mu = mpdqmc.calcPotentialForDensity(-1, 1, 1, 10, 1e-6)