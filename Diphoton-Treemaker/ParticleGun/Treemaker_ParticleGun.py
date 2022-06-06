import ROOT
from ROOT import *
import numpy
import math
import sys
import array
import os
import random
import Helper
#gROOT.SetBatch(kTRUE)

dir_path = os.path.dirname(os.path.realpath(__file__)) #Get directory where this Treemaker.py is located
gInterpreter.Declare('#include "{}/RDF_Functions.h"'.format(dir_path))

saveTreeFolder = "/cms/sclark-2/DiPhotonsTrees/ParticleGun/" 

#ROOT.ROOT.EnableImplicitMT()
RDF = ROOT.ROOT.RDataFrame

def Treemaker(folder, Dataset, isData):
  global saveTreeFolder
  Name = Dataset
  oF = TFile(Name+".root", "recreate")
  oF.Write()
  oF.Close()
  tree = "flattener/tree"
  Chain = TChain(tree)
  fcount = 0
  for path, subdirs, files in os.walk(folder):
    for name in files:
      File = os.path.join(path, name)
      if (File.endswith(".root") and "flat" in File and "RUCLU" not in name):
        if(os.path.getsize(File) > 100):
            #print os.path.join(path, name)
            Chain.Add(File)
            fcount += 1
            #if fcount > 10: break
  print("{} FILES".format(fcount))

  W = 1.
  #if("16" in year): dpindex, eleindex = 13, 101
  #if("17" in year): dpindex, eleindex = 0, 6
  #if("18" in year): dpindex, eleindex = 0, 3
  Branches = [
      ["pico_nom", 1, 1., W],
      ["pico_scale_up", 1, 1.005, W],
      ["pico_scale_down", 1, 0.995, W],
  ]

  for b in Branches:
    
    Rdf = RDF(Chain)
    # Core part of the treemaker: all computations, branches, etc:
    ############
    Rdf = Rdf.Filter("rdfentry_ % "+str(b[1])+" == 0")
    Rdf = Rdf.Define("sf", "return " + str(b[2]) + ";")
    Rdf = Rdf.Define("weight", "return " + str(b[3]) + ";")
    #Get pT all clusters
    Rdf = Rdf.Define("ruclu_pt", "get_pT(moe, ruclu_energy, ruclu_eta, ruclu_phi, pvtx_z, sf)")
    #Get index of two leading clusters in pT
    Rdf = Rdf.Define("pt_idx", "indexes(ruclu_pt)")
    Rdf = Rdf.Define("pt_idx_1", "pt_idx[0]")
    Rdf = Rdf.Define("pt_idx_2", "pt_idx[1]")
    Rdf = Rdf.Filter("pt_idx_1 != pt_idx_2")
    #Xmass, aMass, alpha
    Rdf = Rdf.Define("XM", "get_XM(pt_idx_1, pt_idx_2, moe, ruclu_energy, ruclu_eta, ruclu_phi, pvtx_z, ruclu_pt)")
    Rdf = Rdf.Define("aM", "get_aM(pt_idx_1, pt_idx_2, moe, ruclu_energy)")
    Rdf = Rdf.Define("alpha", "aM/XM")
    #Helper variables for iso
    Rdf = Rdf.Define("clu_to_jet_DR", "get_match_DR(ruclu_pt, ruclu_eta, ruclu_phi, ruclu_energy, jet_pt, jet_eta, jet_phi, jet_energy)")
    Rdf = Rdf.Define("clu_to_jet_index", "get_match_index(ruclu_pt, ruclu_eta, ruclu_phi, ruclu_energy, jet_pt, jet_eta, jet_phi, jet_energy)")
    Rdf = Rdf.Define("jetE", "get_JetE(clu_to_jet_index, clu_to_jet_DR, jet_energy, ruclu_energy)")
    #Iso, masym, deta
    Rdf = Rdf.Define("iso", "ruclu_energy / jetE")
    Rdf = Rdf.Define("masym", "get_Masym(pt_idx_1, pt_idx_2, moe, ruclu_energy)")
    Rdf = Rdf.Define("deta", "get_Deta(pt_idx_1, pt_idx_2, ruclu_eta)")
    #Now just save quantities for leading two clusters
    #Lead Cluster
    Rdf = Rdf.Define("clu1_pt","ruclu_pt[pt_idx_1]")
    Rdf = Rdf.Define("clu1_eta","ruclu_eta[pt_idx_1]")
    Rdf = Rdf.Define("clu1_phi","ruclu_phi[pt_idx_1]")
    Rdf = Rdf.Define("clu1_energy","ruclu_energy[pt_idx_1]")
    Rdf = Rdf.Define("clu1_moe","moe[pt_idx_1]")
    Rdf = Rdf.Define("clu1_iso","iso[pt_idx_1]")
    Rdf = Rdf.Define("clu1_monopho","monophoScores[pt_idx_1]")
    Rdf = Rdf.Define("clu1_dipho","diphoScores[pt_idx_1]")
    Rdf = Rdf.Define("clu1_hadron","hadronScores[pt_idx_1]")
    Rdf = Rdf.Define("clu2_pt","ruclu_pt[pt_idx_2]")
    Rdf = Rdf.Define("clu2_eta","ruclu_eta[pt_idx_2]")
    Rdf = Rdf.Define("clu2_phi","ruclu_phi[pt_idx_2]")
    Rdf = Rdf.Define("clu2_energy","ruclu_energy[pt_idx_2]")
    Rdf = Rdf.Define("clu2_moe","moe[pt_idx_2]")
    Rdf = Rdf.Define("clu2_iso","iso[pt_idx_2]")
    Rdf = Rdf.Define("clu2_monopho","monophoScores[pt_idx_2]")
    Rdf = Rdf.Define("clu2_dipho","diphoScores[pt_idx_2]")
    Rdf = Rdf.Define("clu2_hadron","hadronScores[pt_idx_2]")
    #Get indices of triggers
    #Rdf = Rdf.Define("HLT_DoublePhoton", "triggers[{}]".format(dpindex))
    #Rdf = Rdf.Define("HLT_EleTrig", "triggers[{}]".format(eleindex))
    ############
    # Save to the file we created earlier:
    branchList = ROOT.std.vector('std::string')()
    for k in Helper.keeplist: branchList.push_back(k)
    snapshotOptions = ROOT.RDF.RSnapshotOptions()
    snapshotOptions.fMode = "UPDATE" 
    Rdf.Snapshot(b[0], saveTreeFolder+Name+".root", branchList, snapshotOptions)
