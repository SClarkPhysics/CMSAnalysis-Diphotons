import ROOT
from ROOT import *
import csv
import numpy
import os
import math
import sys
sys.path.append("../../.")
import PlottingPayload as PL
#gROOT.SetBatch()

def doOneInput(N, h, H, S, norm = False):
    toF = TFile("../inputs/"+N+"/"+S+".root", "recreate")
    if norm:
        h.Scale(1./h.Integral())
    toF.cd()
    h.SetName(H)
    h.Write()
    toF.Write()
    toF.Save()
    toF.Close()

LH = []
f = "/cms/sclark/DiphotonAnalysis/CMSSW_11_1_0_pre7/src/CMSAnalysis-Diphotons/Diphoton-Treemaker/HelperFiles/Signal_NEvents_2018.csv"
r = open(f)
for i in r.readlines():
    print i
    LH.append(i.split(','))

def lookup(N):
    X = N.split('A')[0].split('X')[1]
    A = N.split('A')[1].replace('p', '.')
    for r in LH:
        if r[0] == X and r[1] == A: return r[2]


def SaveHists(N, sXr, sX1r, sXvAr, sX, sX1, dX, dX1, dXvA, sX1pu, sX1pd, sX1su, sX1sd):
    PL.MakeFolder("../inputs/"+N)
    with open(N+".txt", 'w') as eff:
        E = sX1.GetEntries()
        G = lookup(N)
        print "eff ("+N+")---> " + str(float(E)/float(G))
        eff.write(str(float(E)/float(G)))
    os.system('mv ' + N + '.txt ../inputs/'+N+"/")
    doOneInput(N, sX1, "h_AveDijetMass_1GeV", "Sig_nominal", True)
    doOneInput(N, sX1pu, "h_AveDijetMass_1GeV", "Sig_PU", True)
    doOneInput(N, sX1pd, "h_AveDijetMass_1GeV", "Sig_PD", True)
    doOneInput(N, sX1su, "h_AveDijetMass_1GeV", "Sig_SU", True)
    doOneInput(N, sX1sd, "h_AveDijetMass_1GeV", "Sig_SD", True)
    doOneInput(N, dX1, "data_XM1", "DATA")
    AE = str(sX.Integral()/sXr.Integral())
    for h in [sXr, sX1r]:
        h.SetFillColor(0)
        h.SetLineColor(1)
    oF = TFile("../inputs/"+N+"/PLOTS_"+N+".root", "recreate")
    sX.Write()
    sX1.Write()
    dX.Write()
    dX1.Write()
    PL.FindAndSetLogMax(sXr, dX)
    PL.FindAndSetLogMax(sX1r, dX1)
    for d in [dX, dX1]:
        d.SetTitle("#alpha window signal efficiency = " + AE)
        d.SetMarkerStyle(20)
        d.SetMarkerColor(1)
        d.SetLineColor(1)
        d.SetLineWidth(1)
        d.SetMarkerSize(0.4)
    L = TLegend(0.11,0.8,0.89,0.89)
    L.SetFillColor(0)
    L.SetLineColor(0)
    L.SetNColumns(2)
    L.AddEntry(dX, "data ("+str(dX.Integral())+" events)", "PL")
    L.AddEntry(sX, s + " (10 fb)", "FL")
    C = TCanvas()
    C.cd()
    C.SetLogy(1)
    dX.Draw("e")
    sXr.Draw("samehist")
    sX.Draw("samehist")
    L.Draw("same")
    C.Print("../inputs/"+N+"/sX.png")
    dX1.Draw("e")
    sX1r.Draw("samehist")
    sX1.Draw("samehist")
    L.Draw("same")
    C.Print("../inputs/"+N+"/sX1M.png")
    C.SetLogy(0)
    sXvAr.Draw("col")
    C.Print("../inputs/"+N+"/sXvA.png")
    dXvA.Draw("col")
    C.Print("../inputs/"+N+"/dXvA.png")
    oF.Write()
    oF.Save()
    oF.Close()

def SaveHists_Interpo(N, sX1, sX1pu, sX1pd, sX1su, sX1sd):
    PL.MakeFolder("../inputs/"+N)
    doOneInput(N, sX1, "h_AveDijetMass_1GeV", "Sig_nominal", True)
    doOneInput(N, sX1pu, "h_AveDijetMass_1GeV", "Sig_PU", True)
    doOneInput(N, sX1pd, "h_AveDijetMass_1GeV", "Sig_PD", True)
    doOneInput(N, sX1su, "h_AveDijetMass_1GeV", "Sig_SU", True)
    doOneInput(N, sX1sd, "h_AveDijetMass_1GeV", "Sig_SD", True)



### PICOTREE DIRECTORIES ###
DATA = ["/cms/xaastorage-2/DiPhotonsTrees/v_first/Run_D_2018.root", "/cms/xaastorage-2/DiPhotonsTrees/v_first/Run_C_2018.root","/cms/xaastorage-2/DiPhotonsTrees/v_first/Run_B_2018.root", "/cms/xaastorage-2/DiPhotonsTrees/v_first/Run_A_2018.root"]
SignalsGenerated = {}
SignalsGenerated["X300A1p5"] = ["/cms/xaastorage-2/DiPhotonsTrees/X300A1p5_2018.root"]
SignalsGenerated["X400A2"] = ["/cms/xaastorage-2/DiPhotonsTrees/X400A2_2018.root"]
SignalsGenerated["X500A2p5"] = ["/cms/xaastorage-2/DiPhotonsTrees/X500A2p5_2018.root"]
SignalsGenerated["X600A3"] = ["/cms/xaastorage-2/DiPhotonsTrees/X600A3_2018.root"]
SignalsGenerated["X750A3p75"] = ["/cms/xaastorage-2/DiPhotonsTrees/X750A3p75_2018.root"]
SignalsGenerated["X1000A5"] = ["/cms/xaastorage-2/DiPhotonsTrees/X1000A5_2018.root"]
SignalsGenerated["X1500A7p5"] = ["/cms/xaastorage-2/DiPhotonsTrees/X1500A7p5_2018.root"]
SignalsGenerated["X2000A10"] = ["/cms/xaastorage-2/DiPhotonsTrees/X2000A10_2018.root"]
SignalsGenerated["X3000A15"] = ["/cms/xaastorage-2/DiPhotonsTrees/X3000A15_2018.root"]
CUTS = [1.0, 3.5, 0.9, 0.5] # masym eta dipho iso
for s in SignalsGenerated:
    (sXr, sX1r, sXvAr) = PL.GetDiphoShapeAnalysis(SignalsGenerated[s], "pico_nom", s, CUTS[0], CUTS[1], CUTS[2], CUTS[3], [0.,0.5], "HLT_DoublePhoton", "puWeight*weight*10.*5.99")
    lA = sXvAr.GetMean(2) - 3.*sXvAr.GetRMS(2)
    hA = sXvAr.GetMean(2) + 3.*sXvAr.GetRMS(2)
    (sXpu, sX1pu, sXvApu) = PL.GetDiphoShapeAnalysis(SignalsGenerated[s], "pico_nom", s, CUTS[0], CUTS[1], CUTS[2], CUTS[3], [lA,hA], "HLT_DoublePhoton", "puWeightUp*weight*10.*5.99")
    (sXpd, sX1pd, sXvApd) = PL.GetDiphoShapeAnalysis(SignalsGenerated[s], "pico_nom", s, CUTS[0], CUTS[1], CUTS[2], CUTS[3], [lA,hA], "HLT_DoublePhoton", "puWeightDown*weight*10.*5.99")
    (sX, sX1, sXvA) = PL.GetDiphoShapeAnalysis(SignalsGenerated[s], "pico_nom", s, CUTS[0], CUTS[1], CUTS[2], CUTS[3], [lA,hA], "HLT_DoublePhoton", "puWeight*weight*10.*5.99")
    (sXsu, sX1su, sXvAsu) = PL.GetDiphoShapeAnalysis(SignalsGenerated[s], "pico_scale_up", s, CUTS[0], CUTS[1], CUTS[2], CUTS[3], [lA,hA], "HLT_DoublePhoton", "weight*10.*5.99")
    (sXsd, sX1sd, sXvAsd) = PL.GetDiphoShapeAnalysis(SignalsGenerated[s], "pico_scale_down", s, CUTS[0], CUTS[1], CUTS[2], CUTS[3], [lA,hA], "HLT_DoublePhoton", "weight*10.*5.99")
    (dX, dX1, dXvA) = PL.GetDiphoShapeAnalysis(DATA, "pico_skim", "data", CUTS[0], CUTS[1], CUTS[2], CUTS[3], [lA,hA], "HLT_DoublePhoton", "1.")
    SaveHists(s, sXr, sX1r, sXvAr, sX, sX1, dX, dX1, dXvA, sX1pu, sX1pd, sX1su, sX1sd)

#Now loop through signals created by interpolater
interp_directory = "../inputs/Interpolations/2018/"
interp_signals = [dirs for subdir, dirs, files in os.walk(interp_directory)][0]
for isig in interp_signals:
  this_dir = interp_directory + isig +""

  nom_file = ROOT.TFile("{}/{}_nom.root".format(this_dir, isig.replace("A","phi")), "read")
  puUp_file = ROOT.TFile("{}/{}_nom_puUp.root".format(this_dir, isig.replace("A","phi")), "read")
  puDown_file = ROOT.TFile("{}/{}_nom_puDown.root".format(this_dir, isig.replace("A","phi")), "read")
  scale_up_file = ROOT.TFile("{}/{}_scale_up.root".format(this_dir, isig.replace("A","phi")), "read")
  scale_down_file = ROOT.TFile("{}/{}_scale_down.root".format(this_dir, isig.replace("A","phi")), "read")

  sX1 = nom_file.Get("{}_XM".format(isig.replace("A","phi")))
  sXpu = puUp_file.Get("{}_XM".format(isig.replace("A","phi")))
  sXpd = puDown_file.Get("{}_XM".format(isig.replace("A","phi")))
  sX1su = scale_up_file.Get("{}_XM".format(isig.replace("A","phi")))
  sX1sd = scale_down_file.Get("{}_XM".format(isig.replace("A","phi")))

  SaveHists_Interpo(isig, sX1, sXpu, sXpd, sX1su, sX1sd)


