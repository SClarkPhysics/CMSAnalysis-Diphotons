import ROOT
from ROOT import *
import csv
import numpy
import os
import math
import sys
import time

RDF = ROOT.RDataFrame.RDataFrame

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../.")
#gROOT.SetBatch()

sample = sys.argv[1]
cat = sys.argv[2]
storage = "/cms/sclark-2/DiPhotonsTrees/"

if("Gun" in sample):
  ww = "ParticleGun"
elif "GJets" in sample:
  ww = "GJets"

if(cat=="m"):
  cat="monopho"
elif(cat=="d"):
  cat="dipho"
elif(cat=="h"):
  cat="hadron"

################################################
#Get DATA
DATA = []
for ff in os.listdir(os.path.join(storage,ww)):
  DATA.append(os.path.join(storage,ww,ff))
 
#DATA = [DATA[0]]
print(DATA)

#Analysis Cuts

dChain = ROOT.TChain("pico_nom")

for df in DATA:
    dChain.Add(df)
Rdf = RDF(dChain)

melow, mehigh = 0.005, 0.5

Rdf = Rdf.Filter("alpha > 0.005 && alpha < 0.3", "Alpha Cut")
Rdf = Rdf.Filter("clu1_moe >= {} && clu1_moe < {}".format(melow,mehigh), "MoE Cut")

#Energy Cut?
#Rdf = Rdf.Filter("clu1_energy > 30 && clu1_energy < 60 && clu2_energy > 30 && clu2_energy < 60", "Energy Cut")

if(cat=="monopho"):
  Rdf = Rdf.Filter("clu1_monopho > 0.99 ", "Classifier Cut")
elif(cat=="dipho"):
  Rdf = Rdf.Filter("clu1_dipho > 0.99", "Classifier Cut")
elif(cat=="hadron"):
  Rdf = Rdf.Filter("clu1_hadron > 0.99", "Classifier Cut")

rep = Rdf.Report()
rep.Print()

sname = "./Trees/{}/cutTree_{}_{}.root".format(ww,ww,cat)
Rdf.Snapshot("tree",sname)
print("File created: {}".format(sname))

