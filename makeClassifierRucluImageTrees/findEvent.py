import os
import sys

source = sys.argv[1]

want_run = sys.argv[2]
want_lumi = sys.argv[3]
want_id = sys.argv[4]

if(source == "GJets"):
  obj="PAT"
  flist = [
          "/GJets_HT-40To100_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16MiniAOD-106X_mcRun2_asymptotic_v13-v1/MINIAODSIM",
          "/GJets_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16MiniAOD-4cores5k_106X_mcRun2_asymptotic_v13-v1/MINIAODSIM",
          "/GJets_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16MiniAOD-106X_mcRun2_asymptotic_v13-v1/MINIAODSIM",
          "/GJets_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16MiniAOD-106X_mcRun2_asymptotic_v13-v1/MINIAODSIM",
          "/GJets_HT-600ToInf_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16MiniAOD-106X_mcRun2_asymptotic_v13-v1/MINIAODSIM",
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
  print("Could not find event with run {}, lumi {} in {} dataset".format(want_run, want_lumi, source))
else:
  print("Found {} event with run {}, lumi {} in file: {}".format(source, want_run, want_lumi, found_file))

print("Now making RUCLU_AOD")
os.system("./makeRUCLU.sh {} {} {} {} {}".format(found_file, obj, want_run, want_lumi, want_id))
os.system("mv outflat.root RucluAODs/{}/{}_{}_{}_{}.root".format(source, source, want_run, want_lumi, want_id))


