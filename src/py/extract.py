import sys
import os
import optparse
import shutil

parser = optparse.OptionParser(usage = "%prog <projdir> <x var> <y var> [Orb1 Orb2 x y z]")
#parser.add_option("--geom", "-g", type = "string", metavar = "FILE", dest = "geom", help = "geometry file which should be used")

(options, args) = parser.parse_args()

if len(args) < 3:
	sys.exit("Not enough arguments given")

projdir = args[0]
keys = args[1:]
res = {}
spacialdep = False
for root, dirs, files in  os.walk(projdir):
	for f in files:
		fnameparts = os.path.splitext(f)
		if fnameparts[1] == ".out" and not os.path.splitext(fnameparts[0])[1] == ".tdm":	
			values = []
			firstline = True
			key = ()
			with open(os.path.realpath(os.path.join(root, f)), "r") as out:
				for line in out:
					if firstline:
						if not line.strip().startswith("General Geometry - Free Format"):
							break
						firstline = False
					if not spacialdep:
						pair = line.split(':')
						quan = pair[0].strip()
						if quan in keys:
							valcol = pair[1].strip()
							if len(pair) > 1 and valcol:
								valpair = valcol.split("+-")
								value = float(valpair[0].strip())
								error = 0.0
								if len(valpair) > 1 and valpair[1].strip():
									error = float(valpair[1].strip())
								idx = keys.index(quan)
								if idx == 0:
									key = (value, error)
								else:
									values.append(value)
									values.append(error)
							else:
								spacialdep = True
					else:
						tokens = line.split()
						if tokens[0][0] == "=":
							spacialdep = False
							break
						match = True
						if len(keys) > 2:
							for i in range(2, len(keys)):
								if i < 4:
									if tokens[i - 2] != keys[i]:
										match = False
										break
								elif i < 7:
									if abs(float(tokens[i - 2]) - float(keys[i])) > 1e-4:
										match = False
										break
								else:
									match = False
									break
						if match:
							for i in range(0, len(tokens) - 4):
								values.append(float(tokens[i]))	
							values.append(float(tokens[6]))
							values.append(float(tokens[8]))
				if len(key) > 0:
					res[key] = values
#res.sort(k = lambda x: x[0][])
for k, v in sorted(res.iteritems()):
	sys.stdout.write(str(k[0]) + "  " + str(k[1]) + "  ")
	for value in v:
		sys.stdout.write(str(value) + "  ")
	sys.stdout.write("\n") 
