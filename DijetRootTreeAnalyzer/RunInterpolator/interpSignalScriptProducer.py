import numpy as np
import sys

xmin, xmax = 320, 2000
xstep = 10
#xmin, xmax = 400,550
#xstep = 50

alphamin, alphamax = 0.005, 0.03
nalphas = 25+1
#nalphas = 5+1
alphalist = np.linspace(alphamin, alphamax, nalphas)
#alphalist = np.array([0.026])
#alphalist = np.array([0.01,0.02,0.026])

xlist = [xx for xx in range(xmin, xmax+xstep, xstep)]

xapairs = []

for mx in xlist:
  for aa in alphalist:
    phimass = mx * aa

    xapairs.append((mx, phimass))

shfile = open("InterpoProducerScript.sh","w")

treeList = ["Sig_nominal","Sig_PU", "Sig_PD", "Sig_SU", "Sig_SD"]


for ii, (xx, pp) in enumerate(xapairs):
  for xora in ["X","alpha"]:
    for tname in treeList:
      shfile.write("python ../python/InterpolatorShapeMaker.py X{}A{} {} {}\n".format(xx, str(round(pp,3)).replace(".","p"), xora, tname))
