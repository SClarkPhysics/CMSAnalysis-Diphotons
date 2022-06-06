import os

fname = "../../getEtas/Trees/2018/belowEta/GoodList.csv"
myfile = open(fname, "r")
Lines = myfile.readlines()

for ii,line in enumerate(Lines):
  if ii==0:continue
  ll = line.split(",")
  run = ll[4][:-1]
  lumi = ll[3]
  iid = ll[2]

  print("python findEvent.py 2018 {} {} {}".format(run, lumi, iid))
  os.system("python findEvent.py 2018 belowEta {} {} {}".format(run, lumi, iid))



