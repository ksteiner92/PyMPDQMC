import os
import sys
import optparse
import ast
import subprocess
import json

if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog <input>")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        sys.exit("Not enough arguments given")

    input = ast.literal_eval(args[0])
    #mpdqmc = MPDQMC(str(input["input"]), int(input["np"]))
    #params = input["params"]
    #dtaumax = params["dtaumax"]

    p = []
    prefix = str(input["prefix"])
    logdir = ""
    if ("logdir" in taskargs):
        logdir = os.path.abspath(taskargs["logdir"])
    for beta in input["beta"]:
        taskargs = input
        taskargs["beta"] = beta
        name = prefix + str(beta)
        params = {}
        ofile = {}
        ofile["value"] = name
        logfile = name + ".log"
        logfile = os.path.append(logdir, logfile)
        ofile["type"] = "str"
        params["ofile"] = ofile
        taskargs["params"] = params
        with open(os.path.abspath(logfile), "w") as log:
            subprocess.Popen(['python', 'task.py', str(taskargs)], stdout=log)