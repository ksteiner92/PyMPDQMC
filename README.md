#PyMPDQMC

A python module for wrapping the example 'ggeom' executable of the quest DQMC (Determinant Quantum Monte Carlo) simulator.
It allows to run different temperature calculations in parallel by automatically submitting it through an sbatch script on a cluster.
Before the actual simulation a a pre-processing can be performed and input parameters can be changed on the fly.
The current supported pre-processing is calculating the chemical potential for a given filling. This is relevant for
non particle hole symmetric systems.

##Usage

The package comes with an 'mpdqmc.py' script which needs as argument an input file. An example input file is given
below. The input file uses the yaml syntax.

```yaml
#number of processes per node
#NOT supported at the moment
np: 6

#beta range configuration
# mandatory
beta:
 logscale: true
 start: 0.001
 end: 100
 steps: 20

#pre-processing
#calculate mu for a given rho
#before simulation
# optional
calcmu:
 mu_start: -2.0
 mu_end: 2.0
 rho: 1.0
 epsilon: 1e-6
 #parameters for calcmu
 params:
  nwarm:
   value: 100
   type: int
  npass:
   value: 400
   type: int

#file prefix this simulation should use
#(all input and output files are assigned
#with this prefix)
# mandatory
prefix: kagome.5x5-U1.

#the maximum dtau value the simulation
#should use. This is important for the
#error (O(dtau^2))
# optional
# default: 0.1
dtaumax: 0.1

#template input file from which all
#simulations are derived if no
#${indir}/${prefix}${beta}.in is given
# mandatory
input: kagome.5x5.in

#the directory in which all logfiles are
#stored. Currently the submission script
#is in charge of logging, which means that
#the output should be pipped into the
#${log} variable
# optional
# default: .
logdir: log

#directory where the input files are stored
#or loaded from
# optional
# default: .
indir: in

#directory where the input files are stored
#before any pre-processing was performed.
#Currently the only pre-processing step is
#calcmu.
# optional
# default: .
predir: pre

#the script which is used for submitting the
#jobs. The current supported grid scheduler is
#sun grid engine (qsub). The script gets the
#variables ${casedir} (root directory of the
#simulations), §{log} (path to logfile) and
#${beta} (temperature)
# mandatory
subscript: sub.qsub
```
