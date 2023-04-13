import ROOT
from ROOT import *
from array import array
import os
import numpy
import sys

gROOT.SetBatch()

LUMI = {}
LUMI["2016"] = 3.59
LUMI["2017"] = 4.15
LUMI["2018"] = 5.99
LUMI["RunII"] = sum([LUMI[yy] for yy in LUMI.keys()])

csv=False
if("csv" in sys.argv): csv=True

def MakeFolder(N):
    if not os.path.exists(N):
     os.makedirs(N)

def GetTH(fN):
	
	TH = TGraph()
	TH.SetPoint(TH.GetN(),100., 335515./fN/fN)
	TH.SetPoint(TH.GetN(),150., 69155./fN/fN)
	TH.SetPoint(TH.GetN(),200., 21362.1/fN/fN)
	TH.SetPoint(TH.GetN(),250., 8304.88/fN/fN)
	TH.SetPoint(TH.GetN(),300., 3746.96/fN/fN)
	TH.SetPoint(TH.GetN(),350., 1878.15/fN/fN)
	TH.SetPoint(TH.GetN(),400., 1017.87/fN/fN)
	TH.SetPoint(TH.GetN(),450., 585.983/fN/fN)
	TH.SetPoint(TH.GetN(),500., 353.898/fN/fN)
	TH.SetPoint(TH.GetN(),625., 117.508/fN/fN)
	TH.SetPoint(TH.GetN(),750., 45.9397/fN/fN)
	TH.SetPoint(TH.GetN(),875., 20.1308/fN/fN)
	TH.SetPoint(TH.GetN(),1000., 9.59447/fN/fN)
	TH.SetPoint(TH.GetN(),1125., 4.88278/fN/fN)
	TH.SetPoint(TH.GetN(),1250., 2.61745/fN/fN)
	TH.SetPoint(TH.GetN(),1375., 1.46371/fN/fN)
	TH.SetPoint(TH.GetN(),1500., 0.847454/fN/fN)
	TH.SetPoint(TH.GetN(),1625., 0.505322/fN/fN)
	TH.SetPoint(TH.GetN(),1750., 0.309008/fN/fN)
	TH.SetPoint(TH.GetN(),1875., 0.192939/fN/fN)
	TH.SetPoint(TH.GetN(),2000., 0.122826/fN/fN)
	TH.SetPoint(TH.GetN(),2125., 0.0795248/fN/fN)
	TH.SetPoint(TH.GetN(),2250., 0.0522742/fN/fN)
	TH.SetPoint(TH.GetN(),2375., 0.0348093/fN/fN)
	TH.SetPoint(TH.GetN(),2500., 0.0235639/fN/fN)
	TH.SetPoint(TH.GetN(),2625., 0.0161926/fN/fN)
	TH.SetPoint(TH.GetN(),2750., 0.0109283/fN/fN)
	TH.SetPoint(TH.GetN(),2875., 0.00759881/fN/fN)
	TH.SetPoint(TH.GetN(),3000., 0.00531361/fN/fN)
	return TH

def AddCMSLumi(pad, fb, extra):
	cmsText     = "CMS " + extra
	cmsTextFont   = 61  
	lumiTextSize     = 0.45
	lumiTextOffset   = 0.15
	cmsTextSize      = 0.5
	cmsTextOffset    = 0.15
	H = pad.GetWh()
	W = pad.GetWw()
	l = pad.GetLeftMargin()
	t = pad.GetTopMargin()
	r = pad.GetRightMargin()
	b = pad.GetBottomMargin()
	e = 0.025
	pad.cd()
	lumiText = str(fb)+" fb^{-1} (13 TeV)"
	latex = TLatex()
	latex.SetNDC()
	latex.SetTextAngle(0)
	latex.SetTextColor(kBlack)	
	extraTextSize = 0.76*cmsTextSize
	latex.SetTextFont(42)
	latex.SetTextAlign(31) 
	latex.SetTextSize(lumiTextSize*t)	
	latex.DrawLatex(1-r,1-t+lumiTextOffset*t,lumiText)
	pad.cd()
	latex.SetTextFont(cmsTextFont)
	latex.SetTextSize(cmsTextSize*t)
	latex.SetTextAlign(11)
	latex.DrawLatex(0.1265, 0.825, cmsText)
	pad.Update()

def AddAlphaRange(pad, al, ah):
  sl = "{:.5f}".format(al)
  sh = "{:.5f}".format(ah)
  aText     = "%s < #alpha #leq %s"%(sl,sh)
  lumiTextSize     = 0.45
  lumiTextOffset   = 0.15
  H = pad.GetWh()
  W = pad.GetWw()
  l = pad.GetLeftMargin()
  t = pad.GetTopMargin()
  r = pad.GetRightMargin()
  b = pad.GetBottomMargin()
  e = 0.025
  latex = TLatex()
  latex.SetNDC()
  latex.SetTextAngle(0)
  latex.SetTextColor(kBlack)	
  latex.SetTextFont(42)
  latex.SetTextAlign(31) 
  latex.SetTextSize(lumiTextSize*t)	
  pad.cd()
  latex.SetTextAlign(11)
  latex.DrawLatex(0.1265, 1-t+lumiTextOffset*t, aText)
  pad.Update()

def AddSignalAlphaRange(pad, sa):
  ssa = "{:.3f}".format(sa)
  aText = "Signal  #alpha = %s"%(ssa)
  cmsTextSize = 0.5
  cmsTextOffset = 0.15
  cmsTextFont = 61  
  H = pad.GetWh()
  W = pad.GetWw()
  l = pad.GetLeftMargin()
  t = pad.GetTopMargin()
  r = pad.GetRightMargin()
  b = pad.GetBottomMargin()
  e = 0.025
  latex = TLatex()
  latex.SetNDC()
  latex.SetTextAngle(0)
  latex.SetTextColor(kBlack)	
  latex.SetTextFont(62)
  latex.SetTextAlign(31) 
  latex.SetTextSize(cmsTextSize*t)	
  pad.cd()
  latex.SetTextAlign(11)
  latex.DrawLatex(0.125, 0.915, aText)
  pad.Update()

def makeAFillGraph(listx,listy1,listy2,linecolor, fillcolor, fillstyle):

	a_m = array('f', []);
	a_g = array('f', []);

	for i in range(len(listx)):
		a_m.append(listx[i]);
		a_g.append(listy1[i]);
	
	for i in range(len(listx)-1,-1,-1):
		a_m.append(listx[i]);
		a_g.append(listy2[i]);

	gr = ROOT.TGraph(2*len(listx),a_m,a_g);

	gr.SetLineColor(linecolor)
	gr.SetFillColor(fillcolor)
	gr.SetFillStyle(fillstyle)

	return gr

def GetAlphaRange(abin):
  
  bd="/cms/sclark/DiphotonAnalysis/CMSSW_11_1_0_pre7/src/CMSAnalysis-Diphotons/DijetRootTreeAnalyzer/inputs/Shapes_fromGen/alphaBinning/{}/".format(abin)

  low,hi = 0,0

  found=False
  for dd in os.listdir(bd):
    if(dd.startswith("X")):
      for ff in os.listdir(os.path.join(bd,dd)):
        if(ff=="arange.txt"):
          myf = open(os.path.join(bd,dd,ff),"r")
          myrange = myf.readline()
          found=True
          break
      if(found): break

  lr=myrange.split(",")
  low,hi = float(lr[0]),float(lr[1])
  
  return low,hi

def MakeLimitPlot(thisxs):
  global csv
  if(csv==True): cfile = open("LimitCSV/limits.csv","w")
  sxs = str(thisxs).replace(".","p")
  #wd = "int_{}_fb".format(sxs)
  wd = "int_1_fb_fixalpha".format(sxs)
  combine_dir = "combineOutput/{}/".format(wd)
  #combine_dir = "combineOutput/int_100_fb/"
  xs=1.
  xs_norm = 1.
  #if("fb" in combine_dir):
  #  sxs = combine_dir.split("_")[-2]
  #  xs = float(sxs.replace("p","."))
  #else: xs = 1.
  scale = xs/xs_norm

  gen_xs = [300,400,500,600,750,1000,1500,2000,3000]
  gen_alphas = [0.005,0.01,0.015,0.02,0.025]

  alphas = []
  flist = []
  for ff in os.listdir(combine_dir):
    sf = ff.split("_")
    xa = sf[1]
    #print(os.path.join(combine_dir,ff))
    this_x = int(xa[1:xa.find("A")])
    this_phi = float(xa[xa.find("A")+1 : ].replace("p","."))
    this_alpha = round(this_phi / float(this_x),3)
    if(this_alpha > 0.025):continue
    #if(this_alpha != 0.009):continue
    #if(this_x not in gen_xs or this_alpha not in gen_alphas): continue   #Ignore interpolated
    alphas.append(this_alpha)
    flist.append([this_x, this_alpha, os.path.join(combine_dir, ff)])

  alphas = sorted(set(alphas))
  print(alphas)
  nflist = numpy.array( [ numpy.array(xi) for xi in flist ] ) #Convert to np array for later selection

  #All Signals
  #for x,a,f in flist:
  #  print(x,a,f)

  ct = 0
  #for xm,alpha,fil in nflist:
  ct += 1
  #if (ct > 1) : break

  lset = list(alphas)

  for sig_alpha in lset:

    print("Starting alpha={}".format(sig_alpha))

    useflist = nflist[ nflist[:,1]==str(sig_alpha) ] #select alpha
    useflist = [ (int(xx), float(aa), str(ff)) for (xx,aa,ff) in useflist ] #Convert back to python list, convert x, alpha to int, float
    useflist.sort(key=lambda row: row[0]) #sort by xmass

    x = []
    obs = []
    exp = []
    p1 = []
    m1 = []
    p2 = []
    m2 = []

    print("Num points: {}".format(len(useflist)))

    for [xx,aa,ff] in useflist:
      if(aa != sig_alpha): continue
      #print(xx,aa,ff)

      #F = TFile('combineOutput/{}/X{}.root'.format(year,m))
      F = TFile(ff)
      try:
        T = F.Get("limit")
        n = T.GetEntries()
      except AttributeError:
        print("Trouble with {}, Skipping.".format(F.GetName()))
        continue
      if n == 6:
        x.append(float(xx))
        T.GetEntry(5)
        obs.append(T.limit*scale)
        T.GetEntry(0)
        m2.append(T.limit*scale)
        T.GetEntry(1)
        m1.append(T.limit*scale)
        T.GetEntry(2)
        exp.append(T.limit*scale)
        T.GetEntry(3)
        p1.append(T.limit*scale)
        T.GetEntry(4)
        p2.append(T.limit*scale)

    bot,top = 0.005, 5000.
    LimitPlot = TH2F("LP", ";Four-Photon Resonance Mass (GeV);(pp #rightarrow X #rightarrow #phi#phi #rightarrow (#gamma#gamma)(#gamma#gamma)) #sigma #times B (fb)", 100, 300, 3000, 100, bot, top)
    #LimitPlot = TH2F("LP", ";Four-Photon Resonance Mass (GeV);(pp #rightarrow X #rightarrow #phi#phi #rightarrow (#gamma#gamma)(#gamma#gamma)) #sigma #times B (fb)", 100, 300, 3200, 1000, 0.000005, 50.)
    LimitPlot.SetStats(0)

    #LimitPlot.GetXaxis().SetMoreLogLabels(ROOT.kTRUE)
    #LimitPlot.GetXaxis().SetRangeUser(300,700)

    TH1 = GetTH(1)
    TH3 = GetTH(3)
    TH9 = GetTH(9)

    Obs = TGraph(len(x), numpy.array(x), numpy.array(obs))
    Exp = TGraph(len(x), numpy.array(x), numpy.array(exp))
    Exp.SetLineStyle(2)
    TH1.SetLineStyle(4)
    TH1.SetLineColor(kBlue)
    TH3.SetLineStyle(5)
    TH3.SetLineColor(kBlue)
    TH9.SetLineStyle(6)
    TH9.SetLineColor(kBlue)
    Obs.SetLineColor(kBlack)
    Obs.SetMarkerStyle(20)
    Obs.SetMarkerSize(0.6666)
    Onesig = makeAFillGraph(x,m1,p1,kGreen,kGreen, 1001)
    Twosig = makeAFillGraph(x,m2,p2,kYellow,kYellow, 1001)

    #X_m phi_m obs exp exp+ exp- exp++ exp--
    if(csv):
      for (wx,oo,ee,mm,mm2,pp,pp2) in zip(x, obs, exp, m1, m2, p1, p2):
        cfile.write("{},{},{},{},{},{},{},{}\n".format(wx,wx*aa,oo,ee,pp,mm,pp2,mm2))

    hp = (len(exp)//2)+1
    gx = [x[0],x[hp]]
    gpoints = [exp[hp],exp[hp]]
    gline = TGraph(len(gx), numpy.array(gx), numpy.array(gpoints))
    gline.SetLineStyle(1)
    gline.SetLineColor(kRed)
    gline.SetLineWidth(2)


    L = TLegend(0.52,0.52,0.89,0.89)
    L.SetLineColor(0)
    L.SetFillColor(0)
    L.SetHeader("95% CL Limits")
    L.AddEntry(Obs, "observed", "PL")
    L.AddEntry(Exp, "expected", "PL")
    L.AddEntry(Onesig, "expected #pm 1#sigma", "F")
    L.AddEntry(Twosig, "expected #pm 2#sigma", "F")
    L.AddEntry(TH1, "X #rightarrow #phi#phi #rightarrow (#gamma#gamma)(#gamma#gamma) [f/N = 1]", "L")
    L.AddEntry(TH3, "X #rightarrow #phi#phi #rightarrow (#gamma#gamma)(#gamma#gamma) [f/N = 3]", "L")
    L.AddEntry(TH9, "X #rightarrow #phi#phi #rightarrow (#gamma#gamma)(#gamma#gamma) [f/N = 9]", "L")
    
    linlist = []
    for xx in gen_xs:
      xlin = TLine(xx,bot,xx,top)
      xlin.SetLineColor(15)
      xlin.SetLineStyle(2)
      linlist.append(xlin)

    C = TCanvas()
    C.cd()
    C.SetLogy()
    #C.SetLogx()
    C.SetGrid(1,1)
    LimitPlot.SetTitle("Signal XS = {} fb".format(thisxs))
    LimitPlot.Draw()
    Twosig.Draw("Fsames")
    Onesig.Draw("Fsames")
    TH1.Draw("Lsame")
    TH3.Draw("Lsame")
    TH9.Draw("Lsame")
    Exp.Draw("Lsame")
    #gline.Draw("Lsame")
    Obs.Draw("LPsame")
    #for xl in linlist:
      #xl.Draw("same")
    L.Draw("same")
    AddCMSLumi(gPad, str(LUMI["RunII"]), "Preliminary")
    AddSignalAlphaRange(gPad,  sig_alpha)
    MakeFolder("LimitPlots/{}".format(wd))
    savename="LimitPlots/{}/Lim_RunII_alpha{}.png".format(wd,str(sig_alpha).replace(".","p"))
    #print("Saving plot as: {}".format(savename))
    C.Print(savename)

  return

xs = sys.argv[1]
MakeLimitPlot(xs)

