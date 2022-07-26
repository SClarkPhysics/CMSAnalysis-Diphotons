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
import PlottingPayload as PL
#gROOT.SetBatch()

year = 2018
igen = "g"

try: signalMass = sys.argv[3] #signal mass point, XxxxAaaa, only use for interpolated
except IndexError: print("Getting all generated signal shapes")

xaastorage = "/cms/xaastorage-2/DiPhotonsTrees/"
const_alpha = False #Use this to get signals at one alpha val

################################################

#Analysis Cuts
# masym, eta, dipho, iso
CUTS = [1.0, 3.5, 0.9, 0.5] #Loose
#CUTS = [0.25, 3.5, 0.9, 0.8] #Analysis Cuts

alphabins = numpy.linspace(0,0.03,200)

aa = TH2D("twod","N Sig Events vs. #alpha", 31,0,0.03, len(alphabins)-1, alphabins)
alpha = TH1D("alph","#alpha_{RMS} per alpha",31,0,0.03)
nSigBins = TH2D("nSigBins", "Number of \'Significant Bins\'; #alpha; N Alpha Bins", 31, 0, 0.03, 201,0, 200)

#################################################
#Generated Signals 
if(igen == "g"):

  SignalsGenerated = {}
  #SignalsGenerated["X300A1p5"] = ["/cms/xaastorage-2/DiPhotonsTrees/X300A1p5_{}.root".format(year)]

  #Get all signals
  for ff in os.listdir(xaastorage):
    if(ff[0]=="X" and str(year) in ff and "X200A" not in ff):
      thisxa = ff[ : ff.find("_")]
      this_x = int(thisxa[1:thisxa.find("A")])
      this_phi = float(thisxa[thisxa.find("A")+1:].replace("p","."))
      if(const_alpha and this_phi / this_x != this_alpha): continue
      SignalsGenerated[thisxa] = [os.path.join(xaastorage, ff)]

  fcount = 0
  tcount = 0


  ct = 0
  for s in SignalsGenerated:
    ct += 1
    saveTree = False
    thisx = int(s[1 : s.find("A")])
    thisphi = float(s[s.find("A")+1 :].replace("p","."))

    if(thisphi / thisx > 0.029): continue
    #if(int(thisphi) != 3): continue
    if(thisx !=  3000 ): continue

    if(thisphi / thisx == 0.005): fcount += 1
    if(thisphi / thisx == 0.01): tcount += 1

    print(thisx, thisphi)

    masym, deta, dipho, iso = CUTS[0], CUTS[1], CUTS[2], CUTS[3]
    trigger = "HLT_DoublePhoton"

    Chain = ROOT.TChain("pico_nom")
    for f in SignalsGenerated[s]:
        Chain.Add(f)
    Rdf = RDF(Chain)
    Rdf = Rdf.Filter(trigger+" > 0.")
    Rdf = Rdf.Filter("clu1_pt > 90. && clu2_pt > 90. && masym < " + str(masym) + " && deta <     " + str(deta) + " && clu1_dipho > " + str(dipho) + " && clu2_dipho > " + str(dipho) + " && clu1_iso > " + str(iso) + " && clu2_iso > " + str(iso))

    
    aHist = Rdf.Histo1D(("alpha","alpha", len(alphabins)-1, alphabins), "alpha")
    useHist = aHist.GetValue().Clone()
    NTot = useHist.GetEntries()

    for ii in range(0,len(alphabins)-1):
      #if(ii % (len(alphabins) // 4) == 0): print("{}/{}".format(ii,len(alphabins)))
      lA=alphabins[ii]
      hA=alphabins[ii+1]

      myBin = aHist.FindBin(lA)
      myCount = aHist.GetBinContent(myBin)

      aa.Fill(thisphi/thisx, (lA+hA)/2, myCount)
    
    nBins = 200
    while nBins > 2:
      #print("N BINS: ", nBins)
      abins = numpy.linspace(0,0.03,nBins)
      myHist = aHist.Rebin(len(abins)-1, "rb",abins)
      sigBins = 0
      for ii in range(0,len(abins)-1):
        lA=abins[ii]
        hA=abins[ii+1]
        myBin = myHist.FindBin(lA)
        myCount = myHist.GetBinContent(myBin)
        #print("{} , {}".format(myCount, NTot))
        if(float(myCount) / float(NTot) > 0.25):
          sigBins += 1
      #print("N SIG: ", sigBins)
      nSigBins.Fill(thisphi/thisx, nBins,sigBins)
      nBins -= 1

print(fcount, tcount)
nSigBins.Scale(1/fcount)

outfile = TFile("alphaplot.root","RECREATE")
outfile.cd()
#alpha.GetXaxis().SetTitle("#alpha")
#alpha.GetYaxis().SetTitle("#alpha_{RMS}")
#alpha.Write()
aa.GetXaxis().SetTitle("#alpha")
aa.GetYaxis().SetTitle("Alpha Slice Window")
aa.Write()

profy = aa.ProfileY()
profy.Write()

profx = aa.ProfileX()
profx.Write()

nSigBins.Write()

outfile.Close()

c1 = TCanvas("c","c",800,600)
c1.cd()
nSigBins.SetStats(0)
nSigBins.Draw("COLZ")
c1.Print("alphaplot.png")
 
  
   

    
