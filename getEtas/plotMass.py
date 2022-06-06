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

dChain = ROOT.TChain("tree")
#dChain.Add("./Trees/2018/cutTree.root")
#dChain.Add("./Trees/2018/etaTree.root")
#dChain.Add("./Trees/2018/belowEta/myTree.root")
dChain.Add("./Trees/2018/aboveEta/myTree.root")

etamass = 0.547862

Rdf = RDF(dChain)

#Rdf = Rdf.Define("clu1_mass","clu1_moe * clu1_energy")
#Rdf = Rdf.Define("clu2_mass","clu2_moe * clu2_energy")

histo = Rdf.Histo1D(("clu1_mass","Lead Cluster Mass;Diphoton Mass (GeV);Events", 200,0,2),"clu1_mass")
c1 = TCanvas()
c1.cd()
hh = histo.GetValue().Clone()
hh.SetLineWidth(2)
hh.SetLineColor(ROOT.kBlue)
hh.Draw("hist")

ll = ROOT.TLine(etamass, 0, etamass, hh.GetMaximum())
ll.SetLineColor(12)
ll.SetLineStyle(9)
ll.Draw("same")

#c1.SetLogy()
c1.Print("MassHisto.png")

dhist = Rdf.Histo1D(("dipho_score","Classifier Diphoton Score;Diphoton Score;Events", 100,0.99,1.),"clu1_dipho")
c2 = TCanvas()
c2.cd()
dh = dhist.GetValue().Clone()
dh.SetLineWidth(2)
dh.SetLineColor(ROOT.kBlue)
dh.Draw("hist")

#c2.SetLogy()
c2.Print("DiphoHisto.png")
