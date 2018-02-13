import sys
import optparse
import dqmc.extractor as e
import matplotlib.pyplot as plt

parser = optparse.OptionParser(usage = "%prog <x var> <y var> [Orb1 Orb2 x y z]")
parser.add_option("--o1", type = "int", dest = "orb1", help = "")
parser.add_option("--o2", type = "int", dest = "orb2", help = "")
parser.add_option("--x", type = "float", dest = "x", help = "")
parser.add_option("--y", type = "float", dest = "y", help = "")
parser.add_option("--z", type = "float", dest = "z", help = "")

(options, args) = parser.parse_args()

if len(args) < 2:
    sys.exit("Not enough arguments given")

ext = e.Extractor()
data = ext.extract(args, vars(options))

x = [k.value for k, v in data]
y = [v[0].value for k, v in data]

fig = plt.figure()

ax1 = fig.add_subplot(111)

ax1.set_title(args[0] + " - " + args[1])
ax1.set_xlabel(args[0])
plt.yscale('log')
ax1.set_ylabel(args[1])

ax1.plot(x, y, c='r', label='the data')

leg = ax1.legend()

plt.savefig(args[1])