import os
import sys

evt = sys.argv[1]

fname = "./{}List.csv".format(evt)

for line in open(fname):
  ll = line.split(",")
  run=ll[0]
  lumi=ll[1]
  eid=ll[2][:-1]

  os.system("python findEvent.py GJets {} {} {}".format(run, lumi, eid))
