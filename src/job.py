#!/home/ksteiner/opt/bin/python
import os
import sys
import optparse
import ast
import subprocess

if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog <input>")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        sys.exit("Not enough arguments given")

    input = ast.literal_eval(args[0])

    p = []
    prefix = str(input["prefix"])
    logdir = ""
    if ("logdir" in input):
        logdir = os.path.abspath(input["logdir"])
    betas = input["beta"]
    if (len(betas) == 0):
        sys.exit("No beta values given")
    numdeci = max(str(betas[0])[::-1].find('.'), str(betas[len(betas) - 1])[::-1].find('.'))
    for beta in betas:
        taskargs = input
        taskargs["beta"] = beta
        betastr = ("b{0:." + str(numdeci) + "f}").format(beta)
        name = prefix + betastr
        params = {}
        ofile = {}
        ofile["value"] = name
        logfile = name + ".log"
        logfile = os.path.join(logdir, logfile)
        ofile["type"] = "str"
        params["ofile"] = ofile
        taskargs["params"] = params
        with open(os.path.abspath(logfile), "w") as log:
            subprocess.Popen(['task.py', str(taskargs)], stdout=log)
