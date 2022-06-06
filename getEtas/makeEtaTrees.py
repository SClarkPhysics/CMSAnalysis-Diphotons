import ROOT
from ROOT import *
import csv
import numpy
import os
import math
import sys
import time
import pandas as pd

RDF = ROOT.RDataFrame.RDataFrame

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../.")
gROOT.SetBatch()

year = sys.argv[1]

eta_mass = 0.547862
delta = 0.0005
deltaDown = 0.1
deltaUp = 0.2

dChain = ROOT.TChain("tree")
dChain.Add("./Trees/{}/cutTree.root".format(year))

Rdf = RDF(dChain)

Rdf = Rdf.Define("clu1_mass","clu1_moe * clu1_energy")
Rdf = Rdf.Define("clu2_mass","clu2_moe * clu2_energy")

#eta
#Rdf = Rdf.Filter("abs(clu1_mass - {}) < {}".format(eta_mass, delta), "Eta Mass Cut")
#sname = "./Trees/{}/etaGoodList.csv".format(year)

#offEta
#sname = "./Trees/{}/offEta/offEtaGoodList.csv".format(year)
#Rdf = Rdf.Filter("abs(clu1_mass - {}) > {} && abs(clu1_mass - {}) < {}".format(eta_mass, deltaDown, eta_mass, deltaUp), "Eta Mass Cut")

#below eta
#Rdf = Rdf.Filter("clu1_mass < {} &&  abs(clu1_mass - {}) > {} && abs(clu1_mass - {}) < {}".format(eta_mass, eta_mass, deltaDown, eta_mass, deltaUp), "Eta Mass Cut")
#sname = "./Trees/{}/belowEta/GoodList.csv".format(year)
#tfname = "./Trees/{}/belowEta/myTree.root".format(year)

#above eta
Rdf = Rdf.Filter("clu1_mass > {} &&  abs(clu1_mass - {}) > {} && abs(clu1_mass - {}) < {}".format(eta_mass, eta_mass, deltaDown, eta_mass, deltaUp), "Eta Mass Cut")
sname = "./Trees/{}/aboveEta/GoodList.csv".format(year)
tfname = "./Trees/{}/aboveEta/myTree.root".format(year)

rep = Rdf.Report()
rep.Print()

#Rdf.Snapshot("tree","./Trees/{}/etaTree.root".format(year))
#Rdf.Snapshot("tree","./Trees/{}/offEta/offetaTree.root".format(year))
Rdf.Snapshot("tree",tfname)

keeplist = ["clu1_mass","clu2_mass","run","lumiSec","id"]
npa = Rdf.AsNumpy(keeplist)
df = pd.DataFrame.from_dict(npa)
df=df.head(100)
df.to_csv(sname, index=False)
print("Saving list as: {}".format(sname))
