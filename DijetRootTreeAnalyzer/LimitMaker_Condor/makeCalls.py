import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

#years = ["2016","2017","2018"]
years = ["RunII"]

alphalist = []
for year in years:
  this_dir = dir_path + "/../inputs/Interpolations/{}/".format(year)

  for ff in os.listdir(this_dir):
    xm = int(ff[1 : ff.find("A")])
    am = float(ff[ff.find("A")+1 : ])
    alpha = round(am/xm,3)

    alphalist.append(alpha)

  alphas = set(alphalist)

  adict = {}
  for aa in alphas:
    #afile = open("CallFiles/Call_alpha{}_{}.sh".format(str(aa).replace(".","p"),year),"w")
    #adict[aa] = afile

    rt_file = open("CallFiles/Call_template.sh","r")
    r_file = open("CallFiles/Call_alpha{}_{}.sh".format(str(aa).replace(".","p"),year),"w")
    for line in rt_file.readlines():
      line = line.replace("ALPHA", "{}".format(str(aa).replace(".","p")))
      line = line.replace("YEAR", "{}".format(year))
      r_file.write(line)

    rct_file = open("condor_submitFiles/runCondor_template.jdl","r")
    rc_file = open("condor_submitFiles/runCondor_alpha{}_{}.jdl".format(str(aa).replace(".","p"),year),"w")
    for line in rct_file.readlines():
      line = line.replace("FILENAME", "Call_alpha{}_{}.sh".format(str(aa).replace(".","p"),year))
      rc_file.write(line)
#
#
#  for ff in os.listdir(this_dir):
#    xm = int(ff[1 : ff.find("A")])
#    am = float(ff[ff.find("A")+1 : ])
#    alpha = round(am/xm,3)
#
#    adict[alpha].write("python ../MakeShapes.py {} i {}\n".format(year, ff))

os.system("chmod +x CallFiles/*.sh")
#os.system("chmod +x runFiles/*.sh")



