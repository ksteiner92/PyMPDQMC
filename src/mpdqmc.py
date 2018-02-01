import optparse
import yaml
import numpy as np

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
    nnodes = int(conf["nodes"])

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

    print "Schedule plan:"
    for i in range(0, len(tasks)):
        print "Node ", i
        for j in range(0, len(tasks[i])):
            print "\tTask ", j, " beta: ", tasks[i][j]


    for i in range(0, len(tasks)):
        cmd = "qsub -v casedir='%s',input='%s', -N 'dqmc-%s' %s"  % (casedir, f, case, args[2])
        print cmd
        os.system(cmd)