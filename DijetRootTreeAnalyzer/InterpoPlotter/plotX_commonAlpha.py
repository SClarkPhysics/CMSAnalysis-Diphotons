import ROOT
import numpy
import os
import math
import sys
sys.path.append("../.")
#import PlottingPayload as PL

#ROOT.gROOT.SetBatch()



def makePlot(year, plot_alpha):
  out_dir = "../inputs/Interpolations/{}/".format(year)

  #tFind = "nom.root"
  #tFind = "nom_puUp.root"
  tFind = "nom_puDown.root"
  #tFind = "scale_up.root"
  #tFind = "scale_down.root"

  outFileName = "OutFiles/{}/alpha{}_{}_plots.png".format(year,str(plot_alpha).replace(".","p"), tFind.replace(".root",""))

  dists = {}
  xmasses = []
  alphas = []
  phimasses = []

  kdists = {}
  kxmasses = []
  kalphas = []
  kphimasses = []

  dirs = []

  for path, subdirs, files in os.walk(out_dir):
    for dd in subdirs:
      #if("X{}A".format(xmass) not in dd): continue
      dirs.append(os.path.join(out_dir, dd))

  for dd in dirs:
    for path, subs, files in os.walk(dd):
      for name in files:
        if(tFind not in name): continue
        File = os.path.join(path, name)
        xamass = name[:name.find("_{}".format(tFind))]
        xmass = int(xamass[1 : xamass.find("phi")])
        phimass = float(xamass[xamass.find("phi")+3 :].replace("p",".") )
        alpha = phimass / xmass
        if xmass % 50 != 0: continue
        if(round(alpha,3) != plot_alpha): continue
        if(xmass in [200, 300, 400, 500, 600, 750, 1000, 1500, 2000]):
          kdists[xamass]=File
          kxmasses.append(xmass)
          kalphas.append(alpha)
          kphimasses.append(phimass)

        else:
          dists[xamass]=File
          xmasses.append(xmass)
          alphas.append(alpha)
          phimasses.append(phimass)

  print("XMASSES", xmasses)
  for (xx,ff) in dists.items():
    print(xx,ff)

  maxx = max(xmasses)
  for xphi, kfile in kdists.items():
    #if xphi in dists:
      dists[xphi] = kfile

  maxes = []
  for xphi, F in dists.items():
    tf = ROOT.TFile(F, "read")
    hname = "{}_XM".format(xphi)
    hist = tf.Get(hname)
    maxes.append(hist.GetMaximum())

  top = 0.11
  top = max(maxes)*1.15
  linelist={}
  allxmasses = set(xmasses + kxmasses)
  for xm in allxmasses:
    lin = ROOT.TLine(xm,0,xm,top)
    linelist[str(xm)] = lin

  c1 = ROOT.TCanvas()
  c1.cd()

  legend = ROOT.TLegend(0.70,0.50,0.90,0.90)

  ct = 0


  for xphi, F in dists.items():
    this_x = int(xphi[1:xphi.find("phi")])
    this_phi = float(xphi[xphi.find("phi")+3 :])
    this_alpha = this_phi / this_x
    #if ct >= 1: break
    known = False
  
    if(this_x in [200,300,400,500,600,750,1000,1500,2000] and this_alpha in [0.005, 0.01, 0.015, 0.02, 0.025, 0.03]):
      known=True

    tf = ROOT.TFile(F, "read")
    hname = "{}_XM".format(xphi)
    hist = tf.Get(hname)

    #if known: continue
    #if known:
    #  for nx in range(0,hist.GetNbinsX()):
    #    print(nx, hist.GetBinLowEdge(nx), hist.GetBinContent(nx))

    #hist.Scale(1/hist.Integral())
    hist.GetXaxis().SetRangeUser(200, 2200)
    hist.GetYaxis().SetRangeUser(0, top)
    hist.SetTitle("{} Dicluster Mass, alpha = {}".format(year, plot_alpha))
    hist.GetXaxis().SetTitle("Dicluster Mass")
    hist.GetYaxis().SetTitle("Entries")
    if known: 
      hist.SetLineColor(ROOT.kBlue)
      hist.SetFillColor(ROOT.kBlue)
    else: 
      hist.SetLineColor(ROOT.kRed)
      hist.SetFillColor(ROOT.kRed)
    hist.SetFillStyle(3001)
    hist.GetXaxis().SetTitleSize(0.175/4)
    hist.GetXaxis().SetLabelSize(0.145/4)
    hist.GetXaxis().SetTitleOffset(1)
    hist.GetYaxis().SetTitleSize(0.175/4)
    hist.GetYaxis().SetLabelSize(0.145/4)
    hist.GetYaxis().SetTitleOffset(1)
    hist.SetStats(0)

    hist.SetDirectory(ROOT.gROOT)

    linelist[str(this_x)].SetLineColor(15)
    linelist[str(this_x)].SetLineStyle(9)
    linelist[str(this_x)].SetLineWidth(1)

    if(ct==0): hist.Draw("hist")
    else: hist.Draw("histsame")
    #linelist[str(this_x)].Draw("same")
    ct+=1

  legend.SetBorderSize(0)
  #legend.Draw("same")
  ROOT.gStyle.SetLegendTextSize(0.035)

  #c1.SetLogy()

  c1.Print(outFileName)
  print("Saving as {}".format(outFileName))


year = sys.argv[1]
if(sys.argv[2] == "all"):
  ROOT.gROOT.SetBatch()
  alphamin, alphamax = 0.005, 0.03
  nalphas = 25+1
  alphalist = numpy.linspace(alphamin, alphamax, nalphas)
  alphalist = [round(float(aa),3) for aa in alphalist]
  print(alphalist)
  for pa in alphalist:
    print("Alpha = {}".format(pa))
    makePlot(year, pa)
    print("\n")

else: 
  pa = float(sys.argv[2])
  makePlot(year, pa)

