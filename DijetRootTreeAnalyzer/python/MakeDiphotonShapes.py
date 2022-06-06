import ROOT
import numpy
import os
import math
import sys
import pandas

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../.")
import PlottingPayload as PL

LUMI = {}
LUMI["2016"] = 36.050
LUMI["2017"] = 39.670
LUMI["2018"] = 59.320

#Analysis cuts, make sure these match MakeShapes.py
#cutString = "masym < 0.25 && clu1_dipho > 0.9 && clu2_dipho > 0.9 && clu1_iso > 0.8 && clu2_iso > 0.8 && clu1_pt > 70 && clu2_pt > 70"
cutString = "masym < 1 && clu1_dipho > 0.9 && clu2_dipho > 0.9 && clu1_iso > 0.5 && clu2_iso > 0.5"

def FindAndSetMax(*args):
  if len(args) == 1: args = args[0]
  maximum = 0.0
  for i in args:
    i.SetStats(0)
    t = i.GetMaximum()
    if t > maximum:
      maximum = t
  for j in args:
    j.GetYaxis().SetRangeUser(0,maximum*1.35)#should be 1.35 (below as well)
    j.SetLineWidth(2)
  return maximum*1.35

def computeBoundingIndices(M, anchors):
  lowI, highI = 0,0

  minlDiff=9999
  minhDiff=9999
  for ind, N in enumerate(anchors):
    if(N < M):
      if (M - N < minlDiff): 
        minlDiff = M - N
        lowI = ind

    elif(N > M):
      if (N - M < minhDiff): 
        minhDiff = N - M
        highI = ind

  return lowI, highI

def integralInterpo(Min, INTS, M, log=True):
  MSS = [float(k) for k in Min]

  SPLINE = 0
  if log:
    IL, IH = computeBoundingIndices(M, MSS)
    TF = ROOT.TF1("tempF", "[1]*TMath::Exp((x-[0])*TMath::Log([3]/[1])/([2]-[0]))", M-50, M+50)
    TF.SetParameter(0, MSS[IL])
    TF.SetParameter(1, INTS[IL])
    TF.SetParameter(2, MSS[IH])
    TF.SetParameter(3, INTS[IH])
    SPLINE = TF.Eval(M)

  else:
    LINTS = [numpy.log(INTS) for sl in range(len(INTS.keys()))]
    TG = ROOT.TGraph(len(MSS), numpy.array(MSS), numpy.array(LINTS[sl]))
    TG.SetBit(ROOT.TGraph.kIsSortedX)
    SPLINE = TG.Eval(M)

  return SPLINE

def linearInterpolate(x, x1, y1, x2, y2):
  return y1 + ( (x - x1) * (y2 - y1) ) / (x2 - x1)

def getDenom(my_x, my_phi):
  """
  Get N Events Generated for a known signal
  """
  ### N Events File ###
  infoFile = "/cms/sclark/DiphotonAnalysis/CMSSW_11_1_0_pre7/src/CMSAnalysis-Diphotons/Diphoton-Treemaker/HelperFiles/Signal_NEvents_{}.csv".format(year)
  xm, phim, nevt = numpy.loadtxt(infoFile, delimiter=',', skiprows=1, unpack=True)
  for (x,p,n) in zip(xm, phim, nevt):
    if (x == my_x and p == my_phi):
      return n

def findzerostart(hist,massmax):
  zs = hist.GetXaxis().GetXmax()
  bnum = hist.GetNbinsX()

  for bb in range(hist.GetNbinsX()-2):
    if(hist.GetBinCenter(bb) > massmax and hist.GetBinCenter(bb) > hist.GetMean()):
      if(hist.GetBinContent(bb) == 0 and hist.GetBinContent(bb+1) == 0 and hist.GetBinContent(bb+2) == 0):
        zs = hist.GetBinCenter(bb+1)
        bnum = bb
        break

  return [zs,bnum]

class HC:


  def __init__(self, histArr, massArr):
    self._massArr = massArr
    print("MASSARR: {}".format(massArr))
    self._histArr = histArr
    self._x  = ROOT.RooRealVar("x","x",histArr[0].GetXaxis().GetXmin(),histArr[0].GetXaxis().GetXmax())
    self._x.setBins(histArr[0].GetNbinsX())
    self._histInts = [h.Integral() for h in histArr]
    self._inxhists = []
    self._cutEff = []

  def morph(self, MM, var, nameM, N, wpoint):
    #scaled=True
    self._lowI, self._hiI = computeBoundingIndices(MM, self._massArr)
    print(self._massArr[self._lowI], self._massArr[self._hiI])

    if "alpha" not in var:
      HL = self._histArr[self._lowI].Clone(self._histArr[self._lowI].GetName() + "HL")
      HH = self._histArr[self._hiI].Clone(self._histArr[self._hiI].GetName() + "HH")

    else: 
      HH = self._histArr[self._lowI].Clone(self._histArr[self._lowI].GetName() + "HL")
      HL = self._histArr[self._hiI].Clone(self._histArr[self._hiI].GetName() + "HH")

    inxhists = [HL, HH]
    un = nameM


    print("Bounding Masses: {} - {}".format(self._massArr[self._lowI], self._massArr[self._hiI]))

    if "alpha" in var or wpoint < 1:
      rmass = ROOT.RooRealVar("rm_{}".format(un), "rmass", wpoint, 0., 1.)
    else : 
    #if wpoint != 1: 
      print("WPoint: {}".format(wpoint))
      alpha = (float(MM) - float(self._massArr[self._lowI]))/(float(self._massArr[self._hiI]) - float(self._massArr[self._lowI]))
      tlM, thM = self._massArr[self._lowI], self._massArr[self._hiI]
      lM = min(tlM, thM)
      hM = max(tlM, thM)
      wpoint = float(MM - lM) / float(hM - lM)
      print("Calculating share value: ", lM, hM, MM, wpoint)
      #if wpoint > 1: 
      #  print("MORE THAN 1")
      #  print(lM, hM, alpha, self._massArr)
      #  wpoint=0.5
      rmass = ROOT.RooRealVar("rm_{}".format(un), "rmass", wpoint, 0., 1.)
    #rmass = ROOT.RooRealVar("rm_{}".format(un), "rmass", wpoint, 0., 1.)

    RHL = ROOT.RooDataHist("HL_".format(un), ";DiCluster Mass [GeV];Events/GeV", ROOT.RooArgList(self._x), HL)
    RHLR = ROOT.RooHistPdf("HL_AbsReal_{}".format(un), "", ROOT.RooArgSet(self._x), RHL)
    RHH = ROOT.RooDataHist("HH_{}".format(un), ";DiCluster Mass [GeV];Events/GeV", ROOT.RooArgList(self._x), HH)
    RHHR = ROOT.RooHistPdf("HH_AbsReal_{}".format(un), "", ROOT.RooArgSet(self._x), RHH)

    RHIM = ROOT.RooIntegralMorph("Hmorph_{}".format(un), "", RHHR, RHLR, self._x, rmass)
    self.xframe = self._x.frame(ROOT.RooFit.Title(";DiCluster Mass [GeV];Events/GeV"), ROOT.RooFit.Range(0, 10000))
    #self.xframe = self._x.frame(ROOT.RooFit.Title(";DiCluster Mass [GeV];Events/GeV"), ROOT.RooFit.Range(0, 0.1))
    RHI = RHIM.createHistogram("Hinterpo_{}".format(un), self._x)

    print("IL Int: {}".format(HL.Integral()))
    print("IH Int: {}".format(HH.Integral()))
    print("OUT Int: {}".format(RHI.Integral()))

    nzcount = 0
    for bb in range(HH.GetNbinsX()):
      if(HH.GetBinCenter(bb) > 1100 and HH.GetBinContent(bb) > 0):
        nzcount += 1
        #print(HH.GetBinCenter(bb), HH.GetBinContent(bb))
    print("NZH: {}".format(nzcount))
    nzcount = 0
    for bb in range(HL.GetNbinsX()):
      if(HL.GetBinCenter(bb) > 1100 and HL.GetBinContent(bb) > 0):
        nzcount += 1
        #print(HH.GetBinCenter(bb), HH.GetBinContent(bb))
    print("NZL: {}".format(nzcount))

    ##
    ##
    c1 = ROOT.TCanvas()
    c1.cd()
    ll = ROOT.TLegend(0.6,0.5,0.95,0.75)
    ll.SetBorderSize(0)
    HH.SetTitle("HH")
    HH.SetLineColor(ROOT.kRed)
    HL.SetLineColor(ROOT.kGreen)
    HL.SetLineWidth(2)
    HL.SetTitle("HL")

    ll.AddEntry(HL, "In_Low, Int={:.3f}".format(HL.Integral()))
    ll.AddEntry(HH, "In_High, Int={:.3f}".format(HH.Integral()))
    ##
    rr = RHI.Clone(un+N)
    rr.SetTitle("OUT")
    rr.SetLineColor(ROOT.kBlack)
    ll.AddEntry(rr, "OUT, Int={:.3f}".format(rr.Integral()))
    FindAndSetMax([HH, HL, rr])
    HH.Draw("hist")
    HL.Draw("histsame")
    rr.Draw("histsame")
    ll.Draw("same")
    c1.Print("tc3.png")
    ##

    return RHI.Clone(un+N), inxhists

def getAlphaHists(xtreename, xs, alpha, dists, var, weight):
  print("in getAlphaHists()")
  histos = []
  effs = []
  denoms = []

  for xm in xs:
    phim = xm*alpha
    for xphi,F in dists.items():
      dx = int(xphi[1:xphi.find("A")])
      dphi = float(xphi[xphi.find("A")+1 :].replace("p","."))
      if(dphi/dx == alpha and dx == xm):
        Chain=ROOT.TChain(xtreename)
        Chain.Add(F)
        rdf = ROOT.RDataFrame.RDataFrame(Chain)
        rdf = rdf.Filter("HLT_DoublePhoton > 0", "Trigger")
        rdf = rdf.Filter(cutString)
        if(var != "na" in var):
          hist = rdf.Histo1D( ("alpha","alpha",4000,0,4000), "alpha")
          alphastd = hist.GetStdDev()
          rdf = rdf.Filter("alpha > {} && alpha < {}".format(alpha - alphastd*3, alpha + alphastd*3), "alpha Window")
        num = float(rdf.Count().GetValue())

        xhist = rdf.Histo1D(("xmt","xmt",4000,0,4000), "XM")
        x_mean, x_rms = xhist.GetMean(), xhist.GetStdDev()
        print(x_mean, x_rms)
        rdf = rdf.Filter("XM > {} && XM < {}".format(float(xm)*0.85, x_mean+3*x_rms))
        
        #rdf = rdf.Filter("XM > {} && XM < {}".format(float(xm)*0.85, MAX_XM))

        if(var=="XM"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(X1B)-1, numpy.array(X1B)), var, weight)
        elif(var=="XM_na"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(X1B)-1, numpy.array(X1B)), "XM", weight)
        elif(var=="alpha"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(A1B)-1, numpy.array(A1B)), var, weight)
        elif(var=="alpha_na"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(A1B)-1, numpy.array(A1B)), "alpha", weight)

        effs.append(num / getDenom(int(xm), float(phim)))
        denoms.append(getDenom(int(xm), float(phim)))
        histos.append(myhist.GetValue().Clone())
        del Chain, rdf

  return histos, effs, denoms

def getPhiHists(xtreename, xm, alpha, alphas, dists, var, weight):
  print("in getPhiHists()")
  gphis = []
  histos = []
  effs = []
  denoms = []

  use_alphas = []

  for t_alpha in alphas:
    for xphi,F in dists.items():
      dx = int(xphi[1:xphi.find("A")])
      if(dx != xm): continue
      dphi = float(xphi[xphi.find("A")+1 :].replace("p","."))
      dalpha = dphi / dx
      if(dalpha == t_alpha):
        print(xphi)
        use_alphas.append(dalpha)
        gphis.append(dphi)
        Chain=ROOT.TChain(xtreename)
        Chain.Add(F)
        rdf = ROOT.RDataFrame.RDataFrame(Chain)
        rdf = rdf.Filter("HLT_DoublePhoton > 0", "Trigger")
        rdf = rdf.Filter(cutString)
        if("na" in var):
          hist = rdf.Histo1D( ("alpha","alpha",4000,0,4000), "alpha")
          alphastd = hist.GetStdDev()
          rdf = rdf.Filter("alpha > {} && alpha < {}".format(t_alpha - alphastd*3, t_alpha + alphastd*3), "alpha Window")
        num = float(rdf.Count().GetValue())

        xhist = rdf.Histo1D(("xmt","xmt",4000,0,4000), "XM")
        x_mean, x_rms = xhist.GetMean(), xhist.GetStdDev()
        print(x_mean, x_rms)
        rdf = rdf.Filter("XM > {} && XM < {}".format(float(xm)*0.85, x_mean+3*x_rms))

        #rdf = rdf.Filter("XM > {} && XM < {}".format(float(xm)*0.85, MAX_XM), "xmass cut")

        if(var=="XM"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(X1B)-1, numpy.array(X1B)), var, weight)
        elif(var=="XM_na"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(X1B)-1, numpy.array(X1B)), "XM", weight)
        elif(var=="alpha"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(A1B)-1, numpy.array(A1B)), var, weight)
        elif(var=="alpha_na"): 
          myhist = rdf.Histo1D(("{}_{}_{}".format(var, xm, dphi),var,  len(A1B)-1, numpy.array(A1B)), "alpha", weight)

        effs.append(num / getDenom(int(xm), float(dphi)))
        denoms.append(getDenom(int(xm), float(dphi)))
        histos.append(myhist.GetValue().Clone())
        del Chain, rdf

  try: wp = (alpha - min(use_alphas)) / (max(use_alphas) - min(use_alphas))
  except ZeroDivisionError:
    wp=1
  print(alpha, use_alphas, wp)

  return gphis, histos, effs, denoms, wp


def InterpolateHists(input_x, input_phi, var, xtreename, masslist, lm, him, usehists, usemasses, useeffs, denoms, wpp):

      h1,h2 = usehists[0], usehists[1]
      h1.Scale(1/h1.Integral())
      h2.Scale(1/h2.Integral())
      h1.Sumw2()
      h2.Sumw2()
      scalehists=[h1, h2]

      mp = HC(scalehists, usemasses)

      if(masslist.keys()[0]=='X'):
        x1,phi1,eff1,d1 = masslist['X'][lm], input_phi, useeffs[0], denoms[0]
        x2,phi2,eff2,d2 = masslist['X'][him], input_phi, useeffs[1], denoms[1]
        neweff = linearInterpolate(input_x, x1, eff1, x2, eff2) #This is the final efficiency for new signal
        newNevt = linearInterpolate(input_x, x1, d1, x2, d2) #This is the expected n events for new signal

      elif(masslist.keys()[0]=='phi'):
        x1,phi1,eff1,d1 = input_x, masslist['phi'][lm], useeffs[0], denoms[0]
        x2,phi2,eff2,d2 = input_x, masslist['phi'][him], useeffs[1], denoms[1]
        neweff = linearInterpolate(input_phi, phi1, eff1, phi2, eff2) #This is the final efficiency for new signal
        newNevt = linearInterpolate(input_phi, phi1, d1, phi2, d2) #This is the expected n events for new signal

      print("Efficiency: {} -> {} = {}".format(eff1, eff2, neweff))
      print("NEvt: {} -> {} = {}".format(d1, d2, newNevt))

      this_wp = wpp

      E, newxhists = mp.morph(input_x, var, "{}_{}_{}_{}".format(input_x, input_phi, xtreename, var), "newhist_{}_{}_{}_{}".format(input_x, input_phi, xtreename, var), this_wp)
      E.SetTitle("{}, X {} #phi {} Interpolated Signal".format(var, input_x, input_phi))
      E.Sumw2()


      E.Scale(neweff * newNevt)
      E.Scale(LUMI[year] * XS)
      E.SetName("X{}phi{}_{}".format(input_x, input_phi, var))

      return E, neweff, newNevt

def interpoSignalMaker(o, xtreename, wgt):

  global year, MAX_XM, MAX_ALPHA, nxbins, XS, XB, X1B, A1B
  year = o.year
  in_xphi = o.mass
  if(in_xphi[-2:] == "p0"): 
    in_xphi = in_xphi[:-2] #if input is 'X1000A10p0', input becomes 'X1000A10'
  in_x = float(in_xphi[1 : in_xphi.find("A")])
  in_phi = float(in_xphi[in_xphi.find("A")+1 :].replace("p","."))
  in_alpha = in_phi / in_x
  if(in_x.is_integer()): in_x = int(in_x)
  if(in_phi.is_integer()): in_phi = int(in_phi)

  if(in_alpha > 0.05): 
    print("Resolved signal. Skipping.")
    return

  MAX_XM = int(max(in_x * 3, 2000))
  MAX_ALPHA = 0.05
  nxbins = MAX_XM / 2
  XS = float(o.xs) #fb^-1

  XB = [250.0, 255.0, 261.0, 267.0, 273.0, 279.0, 285.0, 291.0, 297.0, 303.0, 310.0, 317.0, 324.0, 331.0, 338.0, 345.0, 352.0, 360.0, 368.0, 376.0, 384.0, 392.0, 400.0, 409.0, 418.0, 427.0, 436.0, 445.0, 454.0, 464.0, 474.0, 484.0, 494.0, 504.0, 515.0, 526.0, 537.0, 548.0, 560.0, 572.0, 584.0, 596.0, 609.0, 622.0, 635.0, 648.0, 662.0, 676.0, 690.0, 704.0, 719.0, 734.0, 749.0, 765.0, 781.0, 797.0, 814.0, 831.0, 848.0, 866.0, 884.0, 902.0, 921.0, 940.0, 959.0, 979.0, 999.0, 1020.0, 1041.0, 1063.0, 1085.0, 1107.0, 1130.0, 1153.0, 1177.0, 1201.0, 1226.0, 1251.0, 1277.0, 1303.0, 1330.0, 1357.0, 1385.0, 1413.0, 1442.0, 1472.0, 1502.0, 1533.0, 1564.0, 1596.0, 1629.0, 1662.0, 1696.0, 1731.0, 1766.0, 1802.0, 1839.0, 1877.0, 1915.0, 1954.0, 1994.0, 2035.0, 2077.0, 2119.0, 2162.0, 2206.0, 2251.0, 2297.0, 2344.0, 2392.0, 2441.0, 2491.0, 2542.0, 2594.0, 2647.0, 2701.0, 2756.0, 2812.0, 2869.0, 2927.0, 2987.0, 3048.0, 3110.0]
  #X1B = PL.MakeNBinsFromMinToMax(2860, 250., 3110.), in_alpha
  mmin, mmax = 190., 3110.
  X1B = PL.MakeNBinsFromMinToMax(int(mmax - mmin), mmin, mmax)
  #A1B = PL.MakeNBinsFromMinToMax(1000,0,MAX_ALPHA)
  A1B = PL.MakeNBinsFromMinToMax(int(MAX_ALPHA * 4000),0,MAX_ALPHA)
  #print(A1B)

  ### PICOTREE DIRECTORIES ###
  pico_dir = "/cms/xaastorage-2/DiPhotonsTrees/"
  dists = {}
  xmasses = []
  phimasses = []
  alphas = []

  for path, subdirs, files in os.walk(pico_dir):
    for name in files:
      File = os.path.join(path, name)
      if name[0]=="X" and year in name:
        xamass = name[:name.find("_")]
        xmass = int(xamass[1 : xamass.find("A")])
        phimass = float(xamass[xamass.find("A")+1 :].replace("p",".") )

        #if(xamass == "X600A6"): continue
  
        if (File.endswith(".root") and year in name and "v_" not in File):
          if(os.path.getsize(File) > 100):
              dists[xamass]=File
              xmasses.append(xmass)
              phimasses.append(phimass)
              alphas.append(phimass / xmass)

  #Determine if we already have xmass or phi mass
  interpoBool = True
  have_x = False
  have_phi = False
  have_alpha = False

  xphipairs = [] 
  for (xx,pp) in zip(xmasses,phimasses):
    if (pp.is_integer()): pp = str(int(pp))
    else: pp = str(pp).replace(".","p")
    xphipairs.append("X{}A{}".format(xx,pp))

  if(in_x in xmasses): have_x = True
  if(in_phi in phimasses): have_phi=True
  if(in_xphi in xphipairs): interpoBool=False
  if(in_alpha in alphas): have_alpha = True
  if o.force : interpoBool=True

  ###
  if(in_x < min(xmasses) or in_x > max(xmasses)): 
    print("Input X = {} GeV out of X mass range. Doing nothing".format(in_x))
    return
  elif(in_alpha < min(alphas) or in_alpha > max(alphas)): 
    print("Input alpha={} out of alpha mass range. Doing nothing".format(in_alpha))
    return
  ###
  ##

  nud = xtreename[xtreename.find("_")+1 :]
  folderName = "{}inputs/Interpolations/{}/X{}A{}".format(dir_path.replace("python",""),year,in_x,in_phi)
  PL.MakeFolder(folderName)
  if("Up" in wgt ):
    outFileName = "{}inputs/Interpolations/{}/X{}A{}/X{}phi{}_{}_puUp.root".format(dir_path.replace("python",""),year,in_x,in_phi,in_x,in_phi,nud)
  elif("Down" in wgt ):
    outFileName = "{}inputs/Interpolations/{}/X{}A{}/X{}phi{}_{}_puDown.root".format(dir_path.replace("python",""),year,in_x,in_phi,in_x,in_phi,nud)
  else:
    outFileName = "{}inputs/Interpolations/{}/X{}A{}/X{}phi{}_{}.root".format(dir_path.replace("python",""),year,in_x,in_phi,in_x,in_phi,nud)

  ###

  if interpoBool: 

    ivars = ["XM","XM_na", "alpha", "alpha_na"]
    #ivars = ["XM"]

    ##
    myout = ROOT.TFile(outFileName, "RECREATE")
    myout.cd()
    ##

    for ivar in ivars:

      print("\nGetting {} Shape for X {} Phi {} Signal".format(ivar, in_x, in_phi))

      if(have_alpha == True and not o.force): 
        print("Known alpha, unkown X. Interpolating from known alpha signals")
        lowx, hix = computeBoundingIndices(in_x, xmasses)
        print(lowx, hix)

        INPUTM = [xmasses[lowx], xmasses[hix]]
        print(INPUTM)
        myhists, myeffs, mydenoms = getAlphaHists(xtreename, INPUTM, in_alpha, dists, ivar, wgt)
        use_masses = {}
        use_masses["X"] = xmasses
        finalshape, feff, fevt = InterpolateHists(in_x, in_phi, ivar, xtreename, use_masses, lowx, hix, myhists, INPUTM, myeffs, mydenoms, 1)

      elif( (have_x and not have_alpha) or o.force ):
        if( o.force ): print("Forcing Interpolation for known signal")
        else: print("Known X, Unknown alpha. Interpolating from same X mass, nearest phi mass signals")

        lowa, hia = computeBoundingIndices(in_alpha, alphas)

        INPUTM = [alphas[lowa], alphas[hia]]
        myphis, myhists, myeffs, mydenoms, wps = getPhiHists(xtreename, in_x, in_alpha, INPUTM, dists, ivar, wgt)
        print("WPS: {}".format(wps))
        use_masses = {}
        use_masses["phi"] = myphis
        finalshape, feff, fevt = InterpolateHists(in_x, in_phi, ivar, xtreename, use_masses, 0, 1, myhists, myphis, myeffs, mydenoms, wps)

      else:
        print("Unknown X and phi mass. Interpolating twice")
        lowx, hix = computeBoundingIndices(in_x, xmasses) 
        bxs = [xmasses[lowx], xmasses[hix]]
      
        inx_alphahists = []
        calc_effs = []
        calc_denoms = []
        for dox in bxs:
          lowa, hia = computeBoundingIndices(in_alpha, alphas)

          INPUTM = [alphas[lowa], alphas[hia]]
          myphis, myhists, myeffs, mydenoms, wps = getPhiHists(xtreename, dox, in_alpha, INPUTM, dists, ivar, wgt)
          use_masses = {}
          use_masses["phi"] = myphis
          newhist, neweff, newdenom = InterpolateHists(dox, in_phi, ivar, xtreename, use_masses, 0, 1, myhists, myphis, myeffs, mydenoms, wps)
          inx_alphahists.append(newhist)
          calc_effs.append(neweff)
          calc_denoms.append(newdenom)

        use_masses = {}
        use_masses["X"] = xmasses
        #finalshape, feff, fevt = InterpolateHists(in_x, in_phi, ivar, xtreename, use_masses, lowx, hix, inx_alphahists, bxs, calc_effs, calc_denoms, wps)
        finalshape, feff, fevt = InterpolateHists(in_x, in_phi, ivar, xtreename, use_masses, lowx, hix, inx_alphahists, bxs, calc_effs, calc_denoms, 1)

      if(ivar == "XM"):
        with open(folderName + "/{}.txt".format(in_xphi.replace("A","phi")), 'w') as effFile:
            print("eff ("+in_xphi+")---> " + str(feff))
            effFile.write(str(feff))

      finalshape.Write()
    myout.Close()

  else: 
    myout = ROOT.TFile(outFileName, "RECREATE")
    myout.cd()
    print("Known Signal. Getting shapes for {}".format(in_xphi))
    print(in_xphi)
    Chain=ROOT.TChain(xtreename)
    Chain.Add(dists[in_xphi])
    rdf = ROOT.RDataFrame.RDataFrame(Chain)
    rdf = rdf.Filter("HLT_DoublePhoton > 0", "Trigger")
    rdf = rdf.Filter(cutString)

    for var in ["XM", "XM_na", "alpha", "alpha_na"]:
      if("na" in var):
        hist = rdf.Histo1D( ("alpha","alpha",4000,0,4000), "alpha")
        alphastd = hist.GetStdDev()
        rdf = rdf.Filter("alpha > {} && alpha < {}".format(in_alpha - alphastd*3, in_alpha + alphastd*3), "alpha Window")
      num = float(rdf.Count().GetValue())
      rdf = rdf.Filter("XM > {} && XM < {}".format(float(in_x)*0.85, MAX_XM), "xmass cut")

      if(var=="XM"): 
        myhist = rdf.Histo1D(("{}_{}_{}".format(var, in_x, in_phi),var,  len(X1B)-1, numpy.array(X1B)), var, wgt)
      elif(var=="XM_na"): 
        myhist = rdf.Histo1D(("{}_{}_{}".format(var, in_x, in_phi),var,  len(X1B)-1, numpy.array(X1B)), "XM", wgt)
      elif(var=="alpha"): 
        myhist = rdf.Histo1D(("{}_{}_{}".format(var, in_x, in_phi),var,  len(A1B)-1, numpy.array(A1B)), var, wgt)
      elif(var=="alpha_na"): 
        myhist = rdf.Histo1D(("{}_{}_{}".format(var, in_x, in_phi),var,  len(A1B)-1, numpy.array(A1B)), "alpha", wgt)

      t_nevt = getDenom(in_x, in_phi)
      t_eff = num / t_nevt
      shist = myhist.GetValue().Clone("X{}phi{}_{}".format(in_x, in_phi, var))
      shist.Scale(1/shist.Integral())
      shist.Sumw2()
      shist.Scale(t_eff*t_nevt)
      shist.Scale(LUMI[year] * XS)
      shist.Write()

      if(var == "XM"):
        with open(folderName + "/{}.txt".format(in_xphi.replace("A","phi")), 'w') as effFile:
            print("eff ("+in_xphi+")---> " + str(t_eff))
            print(num, t_nevt, t_eff)
            effFile.write(str(t_eff))

    print("Saving as: {}".format(outFileName))
    myout.Close()
    return

  print("Saving file: {}".format(outFileName))

if __name__ == "__main__":
  from argparse import ArgumentParser
  parser = ArgumentParser()
  
  parser.add_argument("--year", required=True, default=2018, help='Run II Year' )
  parser.add_argument("--mass", required=True, default = "X623A17", help='X, Phi mass entered as X123A123' )
  parser.add_argument("--forceinterpo", action="store_true", dest="force", help="Force interpolation of intermediate mass points which are given.")
  parser.add_argument("--xs", required=False, default=10, dest="xs", help="Cross Section to Scale Signals in fb^-1. Default is 10")

  args = parser.parse_args()

  interpoSignalMaker(args, "pico_nom", "puWeight")
  interpoSignalMaker(args, "pico_nom", "puWeightUp")
  interpoSignalMaker(args, "pico_nom", "puWeightDown")
  interpoSignalMaker(args, "pico_scale_up", "puWeight")
  interpoSignalMaker(args, "pico_scale_down", "puWeight")
