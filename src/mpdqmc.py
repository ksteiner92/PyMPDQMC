import optparse
import yaml
import numpy as np
import subprocess

if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog <input>")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        sys.exit("Not enough arguments given")

    with open(args[0]) as fin:
        conf = yaml.load(fin)

    betaconf = conf["beta"]
    nsteps = int(betaconf["steps"])
    startbeta = betaconf["start"]
    endbeta = betaconf["end"]
    logscale = betaconf["logscale"]
    dtaumax = 0.1
    if (dtaumax in betaconf):
        dtaumax = betaconf["dtaumax"]
    ntasks = int(conf["np"])
    input = conf["input"]
    prefix = conf["prefix"]

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

    njobs = nsteps / ntasks
    print njobs
    jobs = []
    n = 0
    for i in range(0, njobs):
        tasks = []
        for j in range(0, ntasks):
            tasks.append(getNextBeta(n))
            print "n: ", n, "node ", i, ": task ", j, " beta: ", getNextBeta(n)
            n += 1
        jobs.append(tasks)
    rest = nsteps % ntasks
    if (rest > 0):
        tasks = []
        for i in range(0, rest):
            tasks.append(getNextBeta(n))
            print "n: ", n, "node ", i, " beta: ", getNextBeta(n)
            n += 1
        jobs.append(tasks)

    """
    ppernode = nsteps / nnodes
    tasks = []
    n = 0
    if (ppernode > 0):
        for i in range(0, nnodes):
            taskspernode = []
            for j in range(0, ppernode):
                taskspernode.append(getNextBeta(n))
                print "n: ", n, "node ", i, ": task ", j, " beta: ", getNextBeta(n)
                n += 1
            tasks.append(taskspernode)
        for i in range(0, (nsteps % nnodes)):
            tasks[i].append(getNextBeta(n))
            print "n: ", n, "node ", i, " beta: ", getNextBeta(n)
            n += 1
    else:
        tasks.append([])
        for i in range(0, nsteps):
            tasks[0].append(getNextBeta(i))
    """
    print "Schedule plan:"
    for i in range(0, len(jobs)):
        print "Node ", i
        for j in range(0, len(jobs[i])):
            print "\tTask ", j, " beta: ", jobs[i][j]

    jobargs = {}
    jobargs["input"] = input
    dtaumax = 0.1
    jobargs["dtaumax"] = dtaumax
    if ("calcmu" in conf):
        jobargs["calcmu"] = conf["calcmu"]

    for i in range(0, len(jobs)):
        taskargs = jobargs
        taskargs["beta"] = jobs[i]
        name = prefix, str(jobs[0])
        print taskargs
        subprocess.Popen(['python', '/home/klaus/dev/mpdqmc/src/job.py', str(taskargs)])
        #subprocess.Popen(['qsub', "-N ", name, 'python /home/klaus/dev/mpdqmc/src/job.py', str(taskargs)])
        #subprocess.Popen(["python", "/home/klaus/dev/mpdqmc/src/job.py", str(taskargs)])
        #params = {}
        #params["ofile"] = prefix, str
        #cmd = "qsub -v casedir='%s',input='%s', -N 'dqmc-%s' %s"  % (casedir, f, case, args[2])
        #print cmd
        #os.system(cmd)