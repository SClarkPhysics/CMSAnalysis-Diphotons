import os
import sys

#year = "2016"
#want_run = '274161'
#want_lumi = '295'
#want_id = '511801563'
year = sys.argv[1].replace(",","")
eoff = sys.argv[2]
want_run = sys.argv[3].replace(",","")
want_lumi = sys.argv[4].replace(",","")
want_id = sys.argv[5].replace(",","")

if(year == "2016"):
  obj="RECO"
  flist = [
          "/DoubleEG/Run2016B-21Feb2020_ver2_UL2016_HIPM-v2/MINIAOD",
          "/DoubleEG/Run2016C-21Feb2020_UL2016_HIPM-v1/MINIAOD",
          "/DoubleEG/Run2016D-21Feb2020_UL2016_HIPM-v1/MINIAOD",
          "/DoubleEG/Run2016E-21Feb2020_UL2016_HIPM-v1/MINIAOD",
          "/DoubleEG/Run2016F-21Feb2020_UL2016-v1/MINIAOD",
          "/DoubleEG/Run2016F-21Feb2020_UL2016_HIPM-v1/MINIAOD",
          "/DoubleEG/Run2016G-21Feb2020_UL2016-v1/MINIAOD",
          "/DoubleEG/Run2016H-21Feb2020_UL2016-v1/MINIAOD",
          ]

elif(year == "2017"):
  obj="RECO"
  flist = [
          "/DoubleEG/Run2017B-09Aug2019_UL2017-v1/MINIAOD",
          "/DoubleEG/Run2017C-09Aug2019_UL2017-v1/MINIAOD",
          "/DoubleEG/Run2017D-09Aug2019_UL2017-v1/MINIAOD",
          "/DoubleEG/Run2017E-09Aug2019_UL2017-v1/MINIAOD",
          "/DoubleEG/Run2017F-09Aug2019_UL2017-v1/MINIAOD",
          ]

elif(year == "2018"):
  obj="PAT"
  flist = [
          "/EGamma/Run2018A-UL2018_MiniAODv2-v1/MINIAOD",
          "/EGamma/Run2018B-UL2018_MiniAODv2-v1/MINIAOD",
          "/EGamma/Run2018C-UL2018_MiniAODv2-v1/MINIAOD",
          "/EGamma/Run2018D-UL2018_MiniAODv2-v2/MINIAOD",
          ]

os.system("rm dasOutput.txt")
for ff in flist:
  os.system("dasgoclient --query \"file,run,lumi dataset={}\" >> dasOutput.txt".format(ff))

found_file = ""
lc = 0
for line in open('dasOutput.txt'):
  lc += 1
  #if lc > 3: break

  line = line[:-1] # remove newline character

  linelist = line.split(" ")
  fname, runs, lumis = linelist[0], linelist[1], linelist[2]

  if(runs[0]=="["): runs = runs[1:-1]
  if(lumis[0]=="["): lumis = lumis[1:-1]

  sruns = runs.split(",")
  slumis = lumis.split(",")

  if(want_run in sruns):
    if(want_lumi in slumis):
      found_file = fname
      break

if(found_file==""):
  print("Could not find event with run {}, lumi {} in {} dataset".format(want_run, want_lumi, year))
  exit()
else:
  print("Found {} event with run {}, lumi {} in file: {}".format(year, want_run, want_lumi, found_file))

print("Now making RUCLU_AOD")
os.system("./makeRUCLU.sh {} {} {} {} {}".format(found_file, obj, want_run, want_lumi, want_id))
#os.system("mv outflat.root RucluAODs/{}_{}_{}_{}.root".format(year, want_run, want_lumi, want_id))
if(eoff == "eta"):
  os.system("mv outflat.root RucluAODs/eta/{}_{}_{}_{}.root".format(year, want_run, want_lumi, want_id))
elif(eoff == "offEta"):
  os.system("mv outflat.root RucluAODs/offEta/{}_{}_{}_{}.root".format(year, want_run, want_lumi, want_id))
elif(eoff == "belowEta"):
  os.system("mv outflat.root RucluAODs/belowEta/{}_{}_{}_{}.root".format(year, want_run, want_lumi, want_id))
elif(eoff == "aboveEta"):
  os.system("mv outflat.root RucluAODs/aboveEta/{}_{}_{}_{}.root".format(year, want_run, want_lumi, want_id))


