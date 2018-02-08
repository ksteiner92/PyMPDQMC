import optparse
import yaml
import numpy as np
import subprocess
import os
import sys

if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog <input>")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        sys.exit("Not enough arguments given")

    for arg in args:
        with open(arg) as fin:
            conf = yaml.load(fin)

        #Configure beta range
        #####################
        betaconf = conf["beta"]
        nsteps = int(betaconf["steps"])
        startbeta = betaconf["start"]
        endbeta = betaconf["end"]
        logscale = betaconf["logscale"]
        dtaumax = 0.1
        if (dtaumax in betaconf):
            dtaumax = betaconf["dtaumax"]

        dbeta =  0
        if logscale:
            dbeta = ((np.log(endbeta) - np.log(startbeta)) / np.log(10)) / float(nsteps - 1)
        else:
            dbeta = (endbeta - startbeta) / float(nsteps - 1)

        def getNextBeta(step):
            if logscale:
                start = np.log(startbeta) / np.log(10.0)
                return 10.0**(start + step * dbeta)
            else:
                return startbeta + i * dbeta

        #Configure schedule plan
        #########################
        ntasks = int(conf["np"])
        njobs = nsteps / ntasks
        jobs = []
        n = 0
        for i in range(0, njobs):
            tasks = []
            for j in range(0, ntasks):
                tasks.append(getNextBeta(n))
                n += 1
            jobs.append(tasks)
        rest = nsteps % ntasks
        if (rest > 0):
            tasks = []
            for i in range(0, rest):
                tasks.append(getNextBeta(n))
                n += 1
            jobs.append(tasks)

        print "Schedule plan:"
        for i in range(0, len(jobs)):
            print "Node ", i
            for j in range(0, len(jobs[i])):
                print "\tTask ", j, " beta: ", jobs[i][j]

        #Generate common job parameters
        ###############################
        casedir = os.path.dirname(os.path.abspath(arg))
        input = conf["input"]
        prefix = conf["prefix"]
        jobargs = {}
        jobargs["input"] = input
        jobargs["dtaumax"] = dtaumax

        #Generate input file, pre-input file and logfile directories
        if ("logdir" in conf):
            logdir = os.path.abspath(os.path.join(casedir, conf["logdir"]))
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            jobargs["logdir"] = logdir
        else:
            jobargs["logdir"] = "."

        if ("indir" in conf):
            indir = os.path.abspath(os.path.join(casedir, conf["indir"]))
            if not os.path.exists(indir):
                os.makedirs(indir)
            jobargs["indir"] = indir
        else:
            jobargs["indir"] = "."

        if ("predir" in conf):
            predir = os.path.abspath(os.path.join(casedir, conf["predir"]))
            if not os.path.exists(predir):
                os.makedirs(predir)
            jobargs["predir"] = predir
        else:
            jobargs["predir"] = "."

        if ("calcmu" in conf):
            jobargs["calcmu"] = conf["calcmu"]

        #Generate job specific parameters and submit the jobs
        #####################################################
        numdeci = max(str(startbeta)[::-1].find('.'), str(endbeta)[::-1].find('.'))
        subscript = conf["subscript"]
        for i in range(0, len(jobs)):
            taskargs = jobargs
            for beta in jobs[i]:
                taskargs["beta"] = beta
                betastr = ("b{0:." + str(numdeci) + "f}").format(beta)
                name = prefix + str(betastr)
                if not os.path.isfile(os.path.abspath(name + ".out")):
                    taskargs["prefix"] = name
                    logfile = os.path.join(logdir, name + ".log")
                    params = {}
                    ofile = {}
                    ofile["value"] = name
                    ofile["type"] = "str"
                    params["ofile"] = ofile
                    taskargs["params"] = params
                    qselect = subprocess.check_output(["qselect", "-N", name, "-s", "RQWTH"])
                    if not qselect:
                        subprocess.Popen(['qsub', '-N', str(name), \
                                          '-v', "log=\"" + logfile + \
                                          "\",casedir='" + casedir + \
                                          "',arg=\"" + str(taskargs) + \
                                          "\",beta=\"" + betastr + "\"",\
                                          str(subscript)])
                    else:
                        print "Job '", name, ", already submitted under '", qselect
                else:
                    print "For job '", name, "', exists a result already (skipping)"

