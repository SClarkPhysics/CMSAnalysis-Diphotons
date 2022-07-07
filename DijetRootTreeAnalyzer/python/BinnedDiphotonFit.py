from optparse import OptionParser
import ROOT as rt
import rootTools
from framework import Config
from array import *
from itertools import *
from operator import *
from WriteDataCard_4J import initializeWorkspace,convertToTh1xHist,convertToMjjHist,applyTurnonFunc,applyTurnonGraph
import os
import random
import sys
import math
import numpy

densityCorr = False

def binnedFit(pdf, data, fitRange='Full', useWeight=False):

    if useWeight:
        fr = pdf.fitTo(data,rt.RooFit.Range(fitRange),rt.RooFit.Extended(True),rt.RooFit.SumW2Error(True),rt.RooFit.Save(),rt.RooFit.Minimizer('Minuit2','migrad'),rt.RooFit.Strategy(2))
        #fr = pdf.fitTo(data,rt.RooFit.Range('1,5'),rt.RooFit.Extended(True),rt.RooFit.SumW2Error(True),rt.RooFit.Save(),rt.RooFit.Minimizer('Minuit2','migrad'),rt.RooFit.Strategy(2))
        migrad_status = fr.status()
        hesse_status = -1
    else:
        nll = pdf.createNLL(data,rt.RooFit.Range(fitRange),rt.RooFit.Extended(True),rt.RooFit.Offset(True))
        m2 = rt.RooMinimizer(nll)
        m2.setStrategy(2)
        m2.setMaxFunctionCalls(100000)
        m2.setMaxIterations(100000)
        migrad_status = m2.minimize('Minuit2','migrad')
        improve_status = m2.minimize('Minuit2','improve')
        hesse_status = m2.minimize('Minuit2','hesse')
        minos_status = m2.minos()
        if hesse_status != 3 :
            hesse_status = m2.minimize('Minuit2','hesse')
        fr = m2.save()
    
    return fr

def effFit(pdf, data, conditionalObs):    
    nll = pdf.createNLL(data,rt.RooFit.Range('Eff'),rt.RooFit.Offset(True),rt.RooFit.ConditionalObservables(conditionalObs))
    m2 = rt.RooMinimizer(nll)
    m2.setStrategy(2)
    m2.setMaxFunctionCalls(100000)
    m2.setMaxIterations(100000)
    migrad_status = m2.minimize('Minuit2','migrad')
    improve_status = m2.minimize('Minuit2','improve')
    hesse_status = m2.minimize('Minuit2','hesse')
    minos_status = m2.minos()
    fr = m2.save()
    return fr

def MakeNBinsFromMinToMax(N,Min,Max):
    BINS = []
    for i in range(N+1):
        BINS.append(Min+(i*(Max-Min)/N))
    return numpy.array(BINS)

def simFit(pdf, data, fitRange, effPdf, effData, conditionalObs):
    
    effNll = effPdf.createNLL(effData,rt.RooFit.Range('Eff'),rt.RooFit.Offset(True),rt.RooFit.ConditionalObservables(conditionalObs))

    fitNll = pdf.createNLL(data,rt.RooFit.Range(fitRange),rt.RooFit.Extended(True),rt.RooFit.Offset(True))

    simNll = rt.RooAddition("simNll", "simNll", rt.RooArgList(fitNll, effNll))
        
    m2 = rt.RooMinimizer(simNll)
    m2.setStrategy(2)
    m2.setMaxFunctionCalls(100000)
    m2.setMaxIterations(100000)
    migrad_status = m2.minimize('Minuit2','migrad')
    improve_status = m2.minimize('Minuit2','improve')
    hesse_status = m2.minimize('Minuit2','hesse')
    minos_status = m2.minos()
    fr = m2.save()

    return fr

def convertSideband(name,w,x):
    if name=="Full":
        return "Full"
    names = name.split(',')
    nBins = (len(x)-1)
    iBinX = -1
    sidebandBins = []
    for ix in range(1,len(x)):
        iBinX+=1
        w.var('mjj').setVal((x[ix]+x[ix-1])/2.)
        inSideband = 0
        for fitname in names:
            inSideband += ( w.var('mjj').inRange(fitname) )
        if inSideband: sidebandBins.append(iBinX)

    sidebandGroups = []
    for k, g in groupby(enumerate(sidebandBins), lambda (i,x):i-x):
        consecutiveBins = map(itemgetter(1), g)
        sidebandGroups.append([consecutiveBins[0],consecutiveBins[-1]+1])
        
    newsidebands = ''
    nameNoComma = name.replace(',','')
        
    for iSideband, sidebandGroup in enumerate(sidebandGroups):
        if not w.var('th1x').hasRange('%s%i'%(nameNoComma,iSideband)):
            w.var('th1x').setRange("%s%i"%(nameNoComma,iSideband),sidebandGroup[0],sidebandGroup[1])
        newsidebands+='%s%i,'%(nameNoComma,iSideband)
    newsidebands = newsidebands[:-1]
    return newsidebands

def convertFunctionToHisto(background_,name_,N_massBins_,massBins_):

    background_hist_ = rt.TH1D(name_,name_,N_massBins_,massBins_)

    for bin in range (0,N_massBins_):
        xbinLow = massBins_[bin]
        xbinHigh = massBins_[bin+1]
        binWidth_current = xbinHigh - xbinLow
        value = background_.Integral(xbinLow , xbinHigh) / binWidth_current
        background_hist_.SetBinContent(bin+1,value)

    return background_hist_

def calculateChi2AndFillResiduals(data_obs_TGraph_,background_hist_,hist_fit_residual_vsMass_,workspace_,prinToScreen_=0,effFit_=False):
    
    N_massBins_ = data_obs_TGraph_.GetN()
    MinNumEvents = 10
    #MinNumEvents = 1
    nParFit = 4
    if workspace_.var('meff_%s'%box).getVal()>0 and workspace_.var('seff_%s'%box).getVal()>0 :
        nParFit = 6
    if workspace_.var('p54_%s'%box) != None or workspace_.var('pm4_%s'%box) != None or workspace_.var('pa4_%s'%box) != None :
       # if workspace_.var('pm4_%s'%box) != None and workspace_.var('pm4_%s'%box).getVal()==0:
           # nParFit = 4
        if workspace_.var('pm4_%s'%box) != None and workspace_.var('pm4_%s'%box).getVal()==0 and workspace_.var('pm3_%s'%box) != None and workspace_.var('pm3_%s'%box).getVal()==0 and workspace_.var('p2_%s'%box) != None and workspace_.var('p2_%s'%box).getVal()==0:
            nParFit = 2
        elif workspace_.var('pm4_%s'%box) != None and workspace_.var('pm4_%s'%box).getVal()==0 and workspace_.var('pm3_%s'%box) != None and workspace_.var('pm3_%s'%box).getVal()==0:
            nParFit = 3
        elif workspace_.var('pm4_%s'%box) != None and workspace_.var('pm4_%s'%box).getVal()==0:
            nParFit = 4
        else:
            nParFit = 5



    print nParFit

    chi2_FullRangeAll = 0
    chi2_PlotRangeAll = 0
    chi2_PlotRangeNonZero = 0
    chi2_PlotRangeMinNumEvents = 0 

    N_FullRangeAll = 0
    N_PlotRangeAll = 0
    N_PlotRangeNonZero = 0
    N_PlotRangeMinNumEvents = 0

    for bin in range (0,N_massBins_):
        ## Values and errors
        value_data = data_obs_TGraph_.GetY()[bin]
        err_low_data = data_obs_TGraph_.GetEYlow()[bin]
        err_high_data = data_obs_TGraph_.GetEYhigh()[bin]
        xbinCenter = data_obs_TGraph_.GetX()[bin] 
        xbinLow = data_obs_TGraph_.GetX()[bin]-data_obs_TGraph_.GetEXlow()[bin] 
        xbinHigh = data_obs_TGraph_.GetX()[bin]+data_obs_TGraph_.GetEXhigh()[bin]
        binWidth_current = xbinHigh - xbinLow
        #value_fit = background_.Integral(xbinLow , xbinHigh) / binWidth_current
        value_fit = background_hist_.GetBinContent(bin+1)
        
        ## Fit residuals
        err_tot_data = 0
        if (value_fit > value_data):
            err_tot_data = err_high_data  
        else:
            err_tot_data = err_low_data
        ###
        #These lines were commented, steven uncommented
        if err_tot_data==0:
          print("Manually setting error")
          err_tot_data = 0.0000001	#when we have infinite denominator in pulls
        ###
        print 'error = ', err_tot_data     
        plotRegions = plotRegion.split(',')
        checkInRegions = [xbinCenter>workspace_.var('mjj').getMin(reg) and xbinCenter<workspace_.var('mjj').getMax(reg) for reg in plotRegions]
        if effFit_: checkInRegions = [xbinCenter>workspace_.var('mjj').getMin('Eff') and xbinCenter<workspace_.var('mjj').getMax('Eff')]
        if any(checkInRegions):
            fit_residual = (value_data - value_fit) / err_tot_data
            err_fit_residual = 1
        else:
            fit_residual = 0
            err_fit_residual = 0

        ## Fill histo with residuals

        hist_fit_residual_vsMass_.SetBinContent(bin+1,fit_residual)
        hist_fit_residual_vsMass_.SetBinError(bin+1,err_fit_residual)

        ## Chi2

        chi2_FullRangeAll += pow(fit_residual,2)
        N_FullRangeAll += 1        
        plotRegions = plotRegion.split(',')
        checkInRegions = [xbinCenter>workspace_.var('mjj').getMin(reg) and xbinCenter<workspace_.var('mjj').getMax(reg) for reg in plotRegions]
        if effFit_: checkInRegions = [xbinCenter>workspace_.var('mjj').getMin('Eff') and xbinCenter<workspace_.var('mjj').getMax('Eff')]
        if any(checkInRegions):
            #print '%i: obs %.0f, exp %.2f, chi2 %.2f'%(bin, value_data* binWidth_current * lumi, value_fit* binWidth_current * lumi, pow(fit_residual,2))
            chi2_PlotRangeAll += pow(fit_residual,2)
            N_PlotRangeAll += 1
            if (value_data > 0):
                chi2_PlotRangeNonZero += pow(fit_residual,2)
                N_PlotRangeNonZero += 1
                if(value_data * binWidth_current * lumi > MinNumEvents):
                    chi2_PlotRangeMinNumEvents += pow(fit_residual,2)
                    N_PlotRangeMinNumEvents += 1
    
    #==================
    # Calculate chi2/ndf
    #==================

    # ndf
    ndf_FullRangeAll = N_FullRangeAll - nParFit    
    ndf_PlotRangeAll = N_PlotRangeAll - nParFit    
    ndf_PlotRangeNonZero = N_PlotRangeNonZero - nParFit    
    ndf_PlotRangeMinNumEvents = N_PlotRangeMinNumEvents - nParFit    

    #ndf for s+b fit, need to subtract 1 due to signal strength (ndf=Nbin-(N_of_nuisances+1))
    if w.var('p1_%s'%box).isConstant() and w.var('p2_%s'%box).isConstant():
    	ndf_FullRangeAll -= 1    
    	ndf_PlotRangeAll -= 1    
    	ndf_PlotRangeNonZero -= 1    
    	ndf_PlotRangeMinNumEvents -=1  

    chi2_ndf_FullRangeAll = chi2_FullRangeAll / ndf_FullRangeAll
    chi2_ndf_PlotRangeAll = chi2_PlotRangeAll / ndf_PlotRangeAll
    chi2_ndf_PlotRangeNonZero = chi2_PlotRangeNonZero / ndf_PlotRangeNonZero
    chi2_ndf_PlotRangeMinNumEvents = chi2_PlotRangeMinNumEvents / ndf_PlotRangeMinNumEvents

    return [chi2_FullRangeAll, ndf_FullRangeAll, chi2_PlotRangeAll, ndf_PlotRangeAll, chi2_PlotRangeNonZero, ndf_PlotRangeNonZero, chi2_PlotRangeMinNumEvents, ndf_PlotRangeMinNumEvents]


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-c','--config',dest="config",type="string",default="config/run2.config",
                  help="Name of the config file to use")
    parser.add_option('-d','--dir',dest="outDir",default="./",type="string",
                  help="Output directory to store cards")
    parser.add_option('-l','--lumi',dest="lumi", default=1.,type="float",
                  help="integrated luminosity in pb^-1")
    parser.add_option('-y','--year',dest="year", default=2018,type="string",
                  help="run II year")
    parser.add_option('--run-min',dest="runMin", default=0,type="int",
                  help="minimum run to consider for trigger efficiency")
    parser.add_option('--run-max',dest="runMax", default=999999,type="int",
                  help="maximum run to consider for trigger efficiency")
    parser.add_option('-b','--box',dest="box", default="CaloDijet",type="string",
                  help="box name")
    parser.add_option('--no-fit',dest="noFit",default=False,action='store_true',
                  help="Turn off fit (useful for visualizing initial parameters)")
    parser.add_option('--fit-region',dest="fitRegion",default="Full",type="string",
                  help="Fit region")
    parser.add_option('--plot-region',dest="plotRegion",default="Full",type="string",
                  help="Plot region")
    parser.add_option('-i','--input-fit-file',dest="inputFitFile", default=None,type="string",
                  help="input fit file")
    parser.add_option('-w','--weight',dest="useWeight",default=False,action='store_true',
                  help="use weight")
    parser.add_option('-s','--signal',dest="signalFileName", default=None,type="string",
                  help="input dataset file for signal pdf")
    parser.add_option('-m','--model',dest="model", default="gg",type="string",
                  help="signal model")
    parser.add_option('--mass',dest="mass", default="750",type="string",
                  help="mgluino")
    parser.add_option('--xsec',dest="xsec", default="1",type="string",
                  help="cross section in pb")
    parser.add_option('-t','--trigger',dest="triggerDataFile", default=None,type="string",
                  help="trigger data file")
    parser.add_option('--l1',dest="l1Trigger", default=False,action='store_true',
                  help="level-1 trigger")
    parser.add_option('--fit-trigger',dest="doTriggerFit", default=False,action='store_true',
                  help="fit trigger")
    parser.add_option('--fit-spectrum',dest="doSpectrumFit", default=False,action='store_true',
                  help="fit spectrum")
    parser.add_option('--sim',dest="doSimultaneousFit", default=False,action='store_true',
                  help="do simultaneous trigger fit")
    parser.add_option('--multi',dest="multi", default=True,action='store_true',
                  help="multiple background pdfs")
    parser.add_option('--write-fit', dest="doWriteFit", default=False, action='store_true',
                  help="save fit as a 1 GeV-binned histogram")
    parser.add_option('--words', dest="CUTSTRING", default=" ~~~~ ~~~~~ ", action='store_true',
                  help="what to write on canvas")

    rt.RooMsgService.instance().setGlobalKillBelow(rt.RooFit.FATAL)
    rt.gStyle.SetPaintTextFormat('+.2f')

    (options,args) = parser.parse_args()
    
    cfg = Config.Config(options.config)
    
    box = options.box
    lumi = options.lumi
    year = options.year
    noFit = options.noFit
    fitRegion = options.fitRegion
    plotRegion = options.plotRegion
    histoName = cfg.getVariables(box, "histoName")

    fitfunc=""
    if("dijet" in options.config): fitfunc="Dijet 5p"
    elif("atlas" in options.config): fitfunc="Atlas"
    elif("power" in options.config): fitfunc="Power"

    if options.signalFileName==None:
        signalFileNames = []
        models = []
        xsecs = []
        colors = []
        styles = []
        masses = []
    else:
        signalFileNames = options.signalFileName.split(",")
        models = options.model.split("_")
        masses = options.mass.split("_")
        xsecs = options.xsec.split("_")
        colors = [rt.kBlue+1, rt.kCyan+1, rt.kViolet+1]
        styles = [2, 4, 6]

    print signalFileNames
    print models
    print masses
    print xsecs


    myTH1 = None
    for f in args:
        if f.lower().endswith('.root'):
            rootFile = rt.TFile(f)
            names = [k.GetName() for k in rootFile.GetListOfKeys()]
            print names
            if histoName in names:
                myTH1 = rootFile.Get(histoName)
    if myTH1 is None:
        print "give a root file as input"

    w = rt.RooWorkspace("w"+box)

    paramNames, bkgs = initializeWorkspace(w,cfg,box,multi=options.multi)
        
    if options.inputFitFile is not None:
        inputRootFile = rt.TFile.Open(options.inputFitFile,"r")
        wIn = inputRootFile.Get("w"+box).Clone("wIn"+box)            
        if wIn.obj("fitresult_extDijetPdf_data_obs") != None:
            frIn = wIn.obj("fitresult_extDijetPdf_data_obs")
        elif wIn.obj("nll_extDijetPdf_data_obs") != None:
            frIn = wIn.obj("nll_extDijetPdf_data_obs")
        elif wIn.obj("fitresult_extDijetPdf_data_obs_with_constr") != None:
            frIn = wIn.obj("fitresult_extDijetPdf_data_obs_with_constr")
        elif wIn.obj("nll_extDijetPdf_data_obs_with_constr") != None:
            frIn = wIn.obj("nll_extDijetPdf_data_obs_with_constr")
        elif wIn.obj("simNll") != None:
            frIn = wIn.obj("simNll")
                        
        print "restoring parameters from fit"
        frIn.Print("V")
        for p in rootTools.RootIterator.RootIterator(frIn.floatParsFinal()):
            w.var(p.GetName()).setVal(p.getVal())
            w.var(p.GetName()).setError(p.getError())

    
    x = array('d', cfg.getBinning(box)[0]) # mjj binning
    
    th1x = w.var('th1x')
    nBins = (len(x)-1)
    th1x.setBins(nBins)

    # get trigger dataset    
    triggerData = None
    # Use uncorrected mjj / pT of wide jets
    corr = '_noCorr'
    if options.triggerDataFile is not None:
        triggerFile = rt.TFile.Open(options.triggerDataFile)
        names = [k.GetName() for k in triggerFile.GetListOfKeys()]
        if 'triggerData' not in names:
            tree = triggerFile.Get("rootTupleTree/tree")    
            tree.SetBranchStatus('*',0)        
            tree.SetBranchStatus('mjj%s'%corr,1)
            tree.SetBranchStatus('passHLT_CaloScoutingHT250',1)
            tree.SetBranchStatus('passHLT_CaloJet40_CaloScouting_PFScouting',1)
            tree.SetBranchStatus('event',1)
            tree.SetBranchStatus('lumi',1)
            tree.SetBranchStatus('run',1)
            tree.SetBranchStatus('PassJSON',1)
            tree.SetBranchStatus('deltaETAjj',1)
            tree.SetBranchStatus('deltaPHIjj',1)
            tree.SetBranchStatus('phiWJ_j1',1)
            tree.SetBranchStatus('phiWJ_j2',1)
            tree.SetBranchStatus('etaWJ_j1',1)
            tree.SetBranchStatus('etaWJ_j2',1)
            tree.SetBranchStatus('pTWJ_j1%s'%corr,1)
            tree.SetBranchStatus('pTWJ_j2%s'%corr,1)
            triggerData = rt.RooDataSet("triggerData","triggerData",rt.RooArgSet(w.var("mjj"),w.cat("cut")))
            # l1 efficiency:
            if options.l1Trigger:#edw deltaETAcut!
                cutString = 'abs(deltaETAjj)<1.1&&abs(etaWJ_j1)<2.5&&abs(etaWJ_j2)<2.5&&pTWJ_j1%s>60&&pTWJ_j2%s>30&&PassJSON&&passHLT_CaloJet40_CaloScouting_PFScouting&&mjj%s>=%i&&mjj%s<%i&&run>=%i&&run<=%i'%(corr,corr,corr,w.var("mjj").getMin("Eff"),corr,w.var("mjj").getMax("Eff"),options.runMin,options.runMax)                
            # hlt efficiency:
            else:
                #cutString = 'abs(deltaETAjj)<1.3&&abs(etaWJ_j1)<2.5&&abs(etaWJ_j2)<2.5&&pTWJ_j1%s>60&&pTWJ_j2%s>30&&PassJSON&&passHLT_L1HTT_CaloScouting_PFScouting&&mjj>=%i&&mjj<%i'%(corr,corr,w.var("mjj").getMin("Eff"),w.var("mjj").getMax("Eff"))
                cutString = 'abs(deltaETAjj)<1.1&&abs(etaWJ_j1)<2.5&&abs(etaWJ_j2)<2.5&&pTWJ_j1%s>60&&pTWJ_j2%s>30&&PassJSON&&passHLT_CaloJet40_CaloScouting_PFScouting&&mjj%s>=%i&&mjj%s<%i&&run>=%i&&run<=%i'%(corr,corr,corr,w.var("mjj").getMin("Eff"),corr,w.var("mjj").getMax("Eff"),options.runMin,options.runMax)
            #set the RooArgSet and save
            tree.Draw('>>elist',cutString,'entrylist')        
            elist = rt.gDirectory.Get('elist')    
            entry = -1
            print 'trigger cut string:', cutString
            while True:
                entry = elist.Next()
                if entry == -1: break
                tree.GetEntry(entry)          
                a = rt.RooArgSet(w.var('mjj'),w.cat('cut'))   
                a.setRealValue('mjj',eval('tree.mjj%s'%corr))
                # l1 efficiency:
                if options.l1Trigger:
                    #a.setCatIndex('cut',min(int(tree.passL1T_HTT125 + tree.passL1T_HTT150 + tree.passL1T_HTT175),1)) # for 2015
                    #a.setCatIndex('cut',min(int(tree.passL1T_HTT120 + tree.passL1T_HTT170 + tree.passL1T_HTT200),1)) # for 2016
                    a.setCatIndex('cut',min(int(tree.passL1T_HTT170),1)) # for 2016 ICHEP: variable called L1T_HTT170 is actually L1_HTT240 and L1T_HTT200 is actually L1T_HTT270 due to bug                  
                # hlt efficiency:
                else:
                    a.setCatIndex('cut',int(tree.passHLT_CaloScoutingHT250))
                
                triggerData.add(a)
                
            triggerOutFile = rt.TFile.Open(options.outDir+"/triggerData.root","recreate")
            triggerOutFile.cd()
            triggerData.Write()
            triggerOutFile.Close()
        else:            
            triggerData = triggerFile.Get("triggerData")
            
        rootTools.Utils.importToWS(w,triggerData)
        h_numerator = rt.TH1D('numerator','numerator',len(x)-1,x)
        h_denominator = rt.TH1D('denominator','denominator',len(x)-1,x)        
        w.data('triggerData').fillHistogram(h_numerator,rt.RooArgList(w.var('mjj')),'cut==1')
        w.data('triggerData').fillHistogram(h_denominator,rt.RooArgList(w.var('mjj')))
        effGraph = rt.TGraphAsymmErrors(h_numerator,h_denominator)
        for i in range(0,len(x)-1):
            eff = effGraph.GetY()[i]
            effUp = effGraph.GetEYhigh()[i]
            effDown = effGraph.GetEYlow()[i]
            print "eff [%i, %i] = %f (%+f/, %+f)" %(x[i],x[i+1],eff,effUp,-effDown)
            if w.var('eff_bin%02d'%(i))!=None:
                if (eff <= 0 or eff >= 1):
                    w.var('eff_bin%02d'%(i)).setVal(1)
                    w.var('eff_bin%02d_Mean'%(i)).setVal(1)
                    w.var('eff_bin%02d'%(i)).setConstant(True)
                else:
                    w.var('eff_bin%02d'%(i)).setVal(eff)
                    w.var('eff_bin%02d_Mean'%(i)).setVal(eff)                    
                w.var('eff_bin%02d_SigmaL'%(i)).setVal(effDown)
                if effUp<=0:
                    w.var('eff_bin%02d_SigmaR'%(i)).setVal(1e-5)
                else:
                    w.var('eff_bin%02d_SigmaR'%(i)).setVal(effUp)
    
    sideband = convertSideband(fitRegion,w,x)
    print 'sideband'
    print sideband
    print 'sideband2'
    plotband = convertSideband(plotRegion,w,x)

    extDijetPdf = w.pdf('extDijetPdf')

    myTH1.Rebin(len(x)-1,'data_obs_rebin',x)
    myRebinnedTH1 = rt.gDirectory.Get('data_obs_rebin')
    myRebinnedTH1.SetDirectory(0)
    
    myRealTH1 = convertToTh1xHist(myRebinnedTH1)        
    
    dataHist = rt.RooDataHist("data_obs","data_obs",rt.RooArgList(th1x), rt.RooFit.Import(myRealTH1))
    dataHist.Print('v')
    
    
    rootTools.Utils.importToWS(w,dataHist)

    if noFit and options.inputFitFile is not None:
        fr = frIn
        fr.Print('v')    
        rootTools.Utils.importToWS(w,fr)
    elif noFit:
        fr = rt.RooFitResult()
        effFr = rt.RooFitResult()
    else:        
        rt.gStyle.SetOptStat(0)
        corrCanvas = rt.TCanvas('c','c',500,500)
        corrCanvas.SetRightMargin(0.15)            
        if not options.doSimultaneousFit:
            if options.triggerDataFile is not None and options.doTriggerFit:
                effFr = effFit(w.pdf('effPdf'),w.data('triggerData'),rt.RooArgSet(w.var('mjj')))           
                rootTools.Utils.importToWS(w,effFr)
                effFr.Print('v')
                effFr.covarianceMatrix().Print('v')
                effFr.correlationMatrix().Print('v')
                corrHistEff = effFr.correlationHist('correlation_matrix_eff')
                
                if options.doSpectrumFit:
                    # setup two-step fit with  hesse pdf:
                    hessePdf = effFr.createHessePdf(rt.RooArgSet(w.var('meff_%s'%box),w.var('seff_%s'%box)))
                    # or create the hesse pdf manually:
                    #covMatrix = effFr.covarianceMatrix()
                    #params = rt.RooArgList()
                    #params.add(w.var('meff_%s'%box))
                    #params.add(w.var('seff_%s'%box))
                    #w.factory('meff_centralvalue[%f]'%w.var('meff_%s'%box).getVal())
                    #w.factory('seff_centralvalue[%f]'%w.var('seff_%s'%box).getVal())
                    #mu = rt.RooArgList()
                    #mu.add(w.var('meff_centralvalue'))
                    #mu.add(w.var('seff_centralvalue'))
                    #hessePdf = rt.RooMultiVarGaussian('hessePdf','hessePdf',params,mu,covMatrix)
                    rootTools.Utils.importToWS(w,effFr)
                    rootTools.Utils.importToWS(w,hessePdf)                
                    w.factory('PROD::extDijetPdfHesse(extDijetPdf,%s)'%(hessePdf.GetName()))
                    extDijetPdf = w.pdf('extDijetPdfHesse')
                    # set up two-step fit with 1D gauss pdfs
                    #w.var('meff_Mean').setVal(w.var('meff_%s'%box).getVal())
                    #w.var('seff_Mean').setVal(w.var('seff_%s'%box).getVal())
                    #w.var('meff_Sigma').setVal(w.var('meff_%s'%box).getError())
                    #w.var('seff_Sigma').setVal(w.var('seff_%s'%box).getError())
                    #extDijetPdf = w.pdf('extDijetPdfGaus')
                
            if options.doSpectrumFit:
                fr = binnedFit(extDijetPdf,dataHist,sideband,options.useWeight)
               # fr = binnedFit(extDijetPdf,dataHist,'6000,7000',options.useWeight)        
                rootTools.Utils.importToWS(w,fr)     
                fr.Print('v')
                fr.Print()
                fr.covarianceMatrix().Print('v')
                fr.correlationMatrix().Print('v')
                corrHist = fr.correlationHist('correlation_matrix')
                corrHist.Draw('colztext')
                corrCanvas.Print(options.outDir+'/corrHist.pdf')
                corrCanvas.Print(options.outDir+'/corrHist.C')
                
                ph = extDijetPdf.createHistogram("h_binned_%s" % box, w.var('mjj'), rt.RooFit.Binning(14000,0.,14000.))
                outtemp = rt.TFile("output/fitted_%s.root" % box, "recreate")
                outtemp.cd()
                ph.Write()
            else:
                fr = rt.RooFitResult()
                
            if options.triggerDataFile is not None and options.doTriggerFit:
                corrHistEff.Draw('colztext')
                corrCanvas.Print(options.outDir+'/corrHistEff.pdf')
                corrCanvas.Print(options.outDir+'/corrHistEff.C')            
        else:            
            fr = simFit(extDijetPdf,dataHist,sideband,w.pdf('effPdf'),w.data('triggerData'),rt.RooArgSet(w.var('mjj')))
            rootTools.Utils.importToWS(w,fr)
            fr.Print('v')    
            fr.covarianceMatrix().Print('v')
            fr.correlationMatrix().Print('v')
            corrHist = fr.correlationHist('correlation_matrix')
            rt.gStyle.SetOptStat(0)
            corrCanvas = rt.TCanvas('c','c',500,500)
            corrCanvas.SetRightMargin(0.15)
            corrHist.Draw('colztext')
            corrCanvas.Print(options.outDir+'/corrHistSim.pdf')
            corrCanvas.Print(options.outDir+'/corrHistSim.C')
        
        total = extDijetPdf.expectedEvents(rt.RooArgSet(th1x))
            

    
    # get signal histo if any
    signalHistos = []
    signalHistosOriginal = []
    signalHistosRebin = []
    signalFiles = []
    for model, mass, xsec, signalFileName in zip(models,masses,xsecs,signalFileNames):
        print model, mass, xsec, signalFileName
        signalFile = rt.TFile.Open(signalFileName)
        signalFiles.append(signalFile)
        names = [k.GetName() for k in signalFile.GetListOfKeys()]
        for name in names:
            d = signalFile.Get(name)
            if isinstance(d, rt.TH1):
               # if name=='h_%s_%i'%(model,float(mass)):
		if name=='h_FourjetMass1GeV':
                    print name
                    d.Scale(float(xsec)*lumi/d.Integral())
                    if options.triggerDataFile is not None:
                        if options.doSimultaneousFit:
                            d_turnon = applyTurnonFunc(d,fr,w)
                            name+='_turnon'
                            d = d_turnon
                        elif not options.noFit and options.doTriggerFit:
                            d_turnon = applyTurnonFunc(d,effFr,w)
                            name+='_turnon'
                            d = d_turnon
                    d.Rebin(len(x)-1,name+'_rebin',x)
                    d_rebin = rt.gDirectory.Get(name+'_rebin')
                    d_rebin.SetDirectory(0)
                    if options.triggerDataFile is not None and not options.doSimultaneousFit and not options.doTriggerFit:
                        d_rebin_turnon = applyTurnonGraph(d_rebin,effGraph)
                        d_rebin = d_rebin_turnon
    
                    signalHistosOriginal.append(d)
                    signalHistosRebin.append(d_rebin)
    
                    d_th1x = convertToTh1xHist(d_rebin)
                    signalHistos.append(d_th1x)        

    asimov = extDijetPdf.generateBinned(rt.RooArgSet(th1x),rt.RooFit.Name('central'),rt.RooFit.Asimov())
        
    opt = [rt.RooFit.CutRange(myRange) for myRange in plotband.split(',')]
    asimov_reduce = asimov.reduce(opt[0])
    dataHist_reduce = dataHist.reduce(opt[0])
    for iOpt in range(1,len(opt)):
        asimov_reduce.add(asimov.reduce(opt[iOpt]))
        dataHist_reduce.add(dataHist.reduce(opt[iOpt]))
        
    rss = 0
    for i in range(0,len(x)-1):
        th1x.setVal(i+0.5)
        predYield = asimov.weight(rt.RooArgSet(th1x))
        dataYield = dataHist_reduce.weight(rt.RooArgSet(th1x))
        rss += float(predYield-dataYield) * float(predYield-dataYield)
        print "%i <= mjj < %i; prediction: %.2f; data %i"  % (x[i],x[i+1],predYield,dataYield)
    print "RSS = ", rss 
        
    rt.TH1D.SetDefaultSumw2()
    
    # start writing output
    rt.gStyle.SetOptStat(0)
    rt.gStyle.SetOptTitle(0)
    c = rt.TCanvas('c','c',600,700)
    rootFile = rt.TFile.Open(options.outDir + '/' + 'Plots_%s'%box + '.root','recreate')
    tdirectory = rootFile.GetDirectory(options.outDir)
    if tdirectory==None:
        print "making directory"
        rootFile.mkdir(options.outDir)
        tdirectory = rootFile.GetDirectory(options.outDir)
        tdirectory.Print('v')
        
    h_th1x = asimov.createHistogram('h_th1x',th1x)
    h_data_th1x = dataHist_reduce.createHistogram('h_data_th1x',th1x)
    
    boxLabel = "%s %s Fit" % (box,fitRegion)
    plotLabel = "%s Projection" % (plotRegion)

    if options.triggerDataFile is not None:        
        #d = rt.TCanvas('d','d',500,400)       
        d = rt.TCanvas('d','d',600,700)
        
        d.Divide(1,2,0,0,0)
    
        pad_1 = d.GetPad(1)
        pad_1.SetPad(0.01,0.36,0.99,0.98)
        pad_1.SetRightMargin(0.05)
        pad_1.SetTopMargin(0.05)
        pad_1.SetLeftMargin(0.175)
        pad_1.SetFillColor(0)
        pad_1.SetBorderMode(0)
        pad_1.SetFrameFillStyle(0)
        pad_1.SetFrameBorderMode(0)

        pad_2 = d.GetPad(2)
        pad_2.SetLeftMargin(0.175)
        pad_2.SetPad(0.01,0.02,0.99,0.37)
        pad_2.SetBottomMargin(0.35)
        pad_2.SetRightMargin(0.05)
        pad_2.SetGridx()
        pad_2.SetGridy()

        pad_1.cd()
        
        binning = rt.RooBinning(w.var('mjj').getMin('Eff'),w.var('mjj').getMax('Eff'))
        xEff = array('d',[w.var('mjj').getMin('Eff')])
        if options.doTriggerFit or options.doSimultaneousFit or options.noFit:
            #plotForLoop = range(int(x[0])+1,int(x[-1]),1)
            plotForLoop = x[1:]
        else:
            plotForLoop = x[1:-1]
        for iBin in plotForLoop:
            if iBin<w.var('mjj').getMax('Eff'):
                binning.addBoundary(iBin)
                xEff.append(iBin)
        xEff.append(w.var('mjj').getMax('Eff'))
        h_numerator = rt.TH1D('numerator','numerator',len(xEff)-1,xEff)
        h_denominator = rt.TH1D('denominator','denominator',len(xEff)-1,xEff)        
        w.data('triggerData').fillHistogram(h_numerator,rt.RooArgList(w.var('mjj')),'cut==1')
        w.data('triggerData').fillHistogram(h_denominator,rt.RooArgList(w.var('mjj')))
        effGraph = rt.TGraphAsymmErrors(h_numerator,h_denominator)
        
        h_numerator_coarse = rt.TH1D('numerator_coarse','numerator_coarse',len(x)-1,x)
        h_denominator_coarse = rt.TH1D('denominator_coarse','denominator_coarse',len(x)-1,x)        
        w.data('triggerData').fillHistogram(h_numerator_coarse,rt.RooArgList(w.var('mjj')),'cut==1')
        w.data('triggerData').fillHistogram(h_denominator_coarse,rt.RooArgList(w.var('mjj')))
        effGraph_coarse = rt.TGraphAsymmErrors(h_numerator_coarse,h_denominator_coarse)
        
        histo = h_numerator.Clone('empty')
        for i in range(1,histo.GetNbinsX()+1):
            histo.SetBinContent(i,0)             
            histo.SetBinError(i,0)                    
        histo.Draw()
        #histo.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),w.var('mjj').getMax('Eff'))
        if options.l1Trigger:
            histo.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),x[15])
        else:            
            #histo.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),x[7])
	    histo.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),x[-1])
        #histo.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),1000)
        histo.SetMinimum(0.)
        histo.SetMaximum(1.1)        
        histo.GetYaxis().SetTitle('Efficiency')
        histo.GetYaxis().SetTitleOffset(1)
        histo.GetYaxis().SetTitleSize(0.07)
        histo.GetYaxis().SetLabelSize(0.05)    
        histo.SetLineColor(rt.kWhite)
        histo.SetMarkerColor(rt.kWhite)
        histo.SetLineWidth(0)
        effGraph.SetMarkerStyle(20)
        effGraph.SetMarkerSize(0.5)
        effGraph.SetMarkerColor(rt.kBlack)
        effGraph.SetLineColor(rt.kBlack)
        effGraph.Draw('pezsame')
    
        effTF1 = w.function('effFunc').asTF(rt.RooArgList(w.var('mjj')))
        if options.doTriggerFit or options.doSimultaneousFit:
            effTF1.Draw("lsame")
        elif w.var('eff_bin%02d'%(i-1))!=None:
            h = histo.Clone('h_eff')
            for i in range(1,histo.GetNbinsX()+1):
                h.SetBinContent(i,w.var('eff_bin%02d'%(i-1)).getVal())
            h.SetLineColor(rt.kGreen) #Tried
            h.SetLineWidth(2)
            h.Draw("histsame")
        effGraph.Draw('pezsame')

        l = rt.TLatex()
        l.SetTextAlign(11)
        l.SetTextSize(0.045)
        l.SetTextFont(42)
        l.SetNDC()
        #l.DrawLatex(0.7,0.96,"%i pb^{-1} (%i TeV)"%(lumi,w.var('sqrts').getVal()/1000.))
        l.DrawLatex(0.73,0.96,"%.1f fb^{-1} (%i TeV)"%(lumi/1000.,w.var('sqrts').getVal()/1000.))     
        # PAS        
        #l.SetTextFont(62)
        #l.SetTextSize(0.055)   
        #l.DrawLatex(0.175,0.96,"CMS")
        #l.SetTextFont(52)
        #l.SetTextSize(0.045)
        #l.DrawLatex(0.3,0.96,"Preliminary")
        #paper
        l.SetTextFont(62)
        l.SetTextSize(0.065)   
        l.DrawLatex(0.22,0.89,"CMS")
        l.SetTextFont(52)
        l.SetTextSize(0.045)
        l.DrawLatex(0.32,0.89,"Preliminary")
        
        #leg = rt.TLegend(0.7,0.7,0.89,0.88)
        leg = rt.TLegend(0.7,0.1,0.89,0.28)
        leg.SetTextFont(42)
        leg.SetFillColor(rt.kWhite)
        leg.SetFillStyle(0)
        leg.SetLineWidth(0)
        leg.SetLineColor(rt.kWhite)
        leg.AddEntry(effGraph,"Data","pe") #Not called
        leg.AddEntry(effTF1,"{} Fit".format(fitfunc),"l")
        leg.Draw()
        
        pave_param = rt.TPaveText(0.45,0.15,0.9,0.25,"NDC")
        pave_param.SetTextFont(42)
        pave_param.SetFillColor(0)
        pave_param.SetBorderSize(0)
        pave_param.SetFillStyle(0)
        pave_param.SetTextAlign(11)
        pave_param.SetTextSize(0.045)
        if w.var('meff_%s'%box).getVal()>0 and w.var('seff_%s'%box).getVal()>0 and (options.doTriggerFit or options.doSimultaneousFit):
            pave_param.AddText("m_{eff}"+" = {0:.2f} #pm {1:.2f}".format(w.var('meff_%s'%box).getVal(), (w.var('meff_%s'%box).getErrorHi() - w.var('meff_%s'%box).getErrorLo())/2.0))
            pave_param.AddText("#sigma_{eff}"+" = {0:.2f} #pm {1:.2f}".format(w.var('seff_%s'%box).getVal(), (w.var('seff_%s'%box).getErrorHi() - w.var('seff_%s'%box).getErrorLo())/2.0))
        elif w.var('eff_bin%02d'%(0)) != None:         
            effValList = []
            effErrHiList = []
            effErrLoList = []
            for i in range(0,len(x)-1):
                if not w.var('eff_bin%02d'%(i)).isConstant():
                    effValList.append(w.var('eff_bin%02d'%(i)).getVal())
                    effErrHiList.append(w.var('eff_bin%02d'%(i)).getErrorHi())
                    effErrLoList.append(w.var('eff_bin%02d'%(i)).getErrorLo())

            valString = ",".join(["%.3f"%(effVal) for effVal in effValList])
            errString = ",".join(["^{%+.1e}_{%+.1e}"%(effErrHi,effErrLo) for effErrHi,effErrLo in zip(effErrHiList,effErrLoList)])
            pave_param.SetTextSize(0.025)
            pave_param.AddText("#epsilon = %s"%valString)
            pave_param.AddText("#delta#epsilon = %s"%errString)
            
        #pave_param.Draw("SAME")

        pad_2.cd()
        
        h_eff = convertFunctionToHisto(effTF1,"h_background",len(x)-1,x)        
        h_eff_residual_vs_mass = rt.TH1D("h_eff_residual_vs_mass","h_eff_residual_vs_mass",len(x)-1,x)
        list_chi2AndNdf_background = calculateChi2AndFillResiduals(effGraph_coarse,h_eff,h_eff_residual_vs_mass,w,0,True)

        if options.l1Trigger:
            h_eff_residual_vs_mass.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),x[15])    
        else:
            #h_eff_residual_vs_mass.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),x[7])
            h_eff_residual_vs_mass.GetXaxis().SetRangeUser(w.var('mjj').getMin('Eff'),x[-1])    
        h_eff_residual_vs_mass.GetYaxis().SetRangeUser(-6.5,6.5)
        h_eff_residual_vs_mass.GetYaxis().SetNdivisions(210,True)
        h_eff_residual_vs_mass.SetLineWidth(1)
        h_eff_residual_vs_mass.SetFillColor(rt.kRed) #Tried
        h_eff_residual_vs_mass.SetLineColor(rt.kBlack)
        
        h_eff_residual_vs_mass.GetYaxis().SetTitleSize(2*0.06)
        h_eff_residual_vs_mass.GetYaxis().SetLabelSize(2*0.05)
        h_eff_residual_vs_mass.GetYaxis().SetTitleOffset(0.5)
        h_eff_residual_vs_mass.GetYaxis().SetTitle('#frac{(Data-Fit)}{#sigma_{Data}}')
        
        h_eff_residual_vs_mass.GetXaxis().SetTitleSize(2*0.06)
        h_eff_residual_vs_mass.GetXaxis().SetLabelSize(2*0.05)
        #h_eff_residual_vs_mass.GetXaxis().SetTitle('m_{jj} [GeV]')
        h_eff_residual_vs_mass.GetXaxis().SetTitle('Dijet mass [GeV]')
        
        h_eff_residual_vs_mass.Draw("histsame")
    
        d.Print(options.outDir+"/eff_mjj_%s_%s.pdf"%(fitRegion.replace(',','_'),box))
        d.Print(options.outDir+"/eff_mjj_%s_%s.C"%(fitRegion.replace(',','_'),box))
        tdirectory.cd()
        d.Write()

    background_pdf = w.pdf('%s_bkg_unbin'%box)
    #print(background_pdf)
    background= background_pdf.asTF(rt.RooArgList(w.var("mjj")),rt.RooArgList(w.var('p0_%s'%box)))
    print("\n\nSTEVEN")
    print(background)
    int_b = background.Integral(w.var("mjj").getMin(),w.var("mjj").getMax())
    # p0_b = w.var('Ntot_%s_bkg'%box).getVal()
    print 'Ntot_%s_bkg'%box + " <<<<<<<<<"
    print("int_b: {}".format(int_b))
    #print("MANUALLY SETTING int_b")
    #int_b = 1e-10
    print("lumi: {}".format(lumi))
    p0_b = w.var('Ntot_%s_bkg'%box).getVal() / (int_b * lumi)
    # print("|===> expected bkg integral: ", w.var('Ntot_%s_bkg'%box).getVal())
    background.SetParameter(0,p0_b)
    
    if options.doWriteFit:
        fnbin = MakeNBinsFromMinToMax(14000, 0., 14000.)
        hb = rt.TH1F("hb_finebin", ";Average Dijet Mass [GeV];Events", len(fnbin)-1, fnbin)
        for j in range(1, hb.GetNbinsX()+1): hb.SetBinContent(j, background.Eval(hb.GetXaxis().GetBinCenter(j)))
        fhb = rt.TFile(options.outDir + "/unbinnedfit_%s.root"%box, "recreate")
        fhb.cd()
        hb.Write()
    
    g_data = rt.TGraphAsymmErrors(myRebinnedTH1)
    
    alpha = 1-0.6827
    for i in range(0,g_data.GetN()):
        N = g_data.GetY()[i]
        binWidth = g_data.GetEXlow()[i] + g_data.GetEXhigh()[i]
        L = 0
        if N!=0:
            L = rt.Math.gamma_quantile(alpha/2,N,1.)
        U = rt.Math.gamma_quantile_c(alpha/2,N+1,1)

        #g_data.SetPointEYlow(i, (N-L))
        #g_data.SetPointEYhigh(i, (U-N))
        #g_data.SetPoint(i, g_data.GetX()[i], N)
        g_data.SetPointEYlow(i, (N-L)/(binWidth * lumi))
        g_data.SetPointEYhigh(i, (U-N)/(binWidth * lumi))
        g_data.SetPoint(i, g_data.GetX()[i], N/(binWidth * lumi))
       

        plotRegions = plotRegion.split(',')
        checkInRegions = [g_data.GetX()[i]>w.var('mjj').getMin(reg) and g_data.GetX()[i]<w.var('mjj').getMax(reg) for reg in plotRegions]
        if not any(checkInRegions):
            g_data.SetPointEYlow(i, 0)
            g_data.SetPointEYhigh(i, 0)
            g_data.SetPoint(i, g_data.GetX()[i], 0)
            
    #h_background = convertFunctionToHisto(background,"h_background",len(x)-1,x)
    h_th1x.Scale(1.0/lumi)
    h_background = convertToMjjHist(h_th1x,x)
    h_fit_residual_vs_mass = rt.TH1D("h_fit_residual_vs_mass","h_fit_residual_vs_mass",len(x)-1,x)
    list_chi2AndNdf_background = calculateChi2AndFillResiduals(g_data,h_background,h_fit_residual_vs_mass,w,0)

    #ccc=rt.TCanvas()
    #ccc.cd()
    #h_background.SetLineColor(rt.kBlack)
    #h_background.Draw("e0")
    #h_fit.SetLineColor(rt.kRed)
    #h_fit.Draw("same")
    #ccc.Print("temp.png")

    g_data.SetMarkerStyle(20)
    g_data.SetMarkerSize(0.9)
    g_data.SetLineColor(rt.kBlack)
    g_data_clone = g_data.Clone('g_data_clone')
    g_data_clone.SetMarkerSize(0)

    
    #myRebinnedTH1.SetLineColor(rt.kWhite)
    #myRebinnedTH1.SetMarkerSize(0)

    # to remove dot at 0 (make it too high)
    for i in range (0,g_data.GetN()):
        if g_data.GetY()[i]==0:
            g_data.SetPoint(i,g_data.GetX()[i], 99999)
                   
    c.Divide(1,2,0,0,0)
    
    pad_1 = c.GetPad(1)
    #PAS
    #pad_1.SetPad(0.01,0.36,0.99,0.98)
    #paper 
    pad_1.SetPad(0.01,0.37,0.99,0.98)
   # pad_1.SetLogy()
    if 'PF' in box or w.var('mjj').getMax() > 526:
        pad_1.SetLogx(1)
    pad_1.SetRightMargin(0.05)
    pad_1.SetTopMargin(0.05)
    pad_1.SetLeftMargin(0.175)
    pad_1.SetFillColor(0)
    pad_1.SetBorderMode(0)
    pad_1.SetFrameFillStyle(0)
    pad_1.SetFrameBorderMode(0)
    
    pad_2 = c.GetPad(2)
    pad_2.SetLeftMargin(0.175)#0.175
    pad_2.SetPad(0.01,0.02,0.99,0.37)#0.37
    pad_2.SetBottomMargin(0.35)
    pad_2.SetRightMargin(0.05)
    pad_2.SetGridx()
    pad_2.SetGridy()
    if 'PF' in box or w.var('mjj').getMax() > 1246:
        pad_2.SetLogx()

    pad_1.cd()
    
    myRebinnedDensityTH1 = myRebinnedTH1.Clone('data_obs_density')
    for i in range(1,nBins+1):
        myRebinnedDensityTH1.SetBinContent(i, myRebinnedTH1.GetBinContent(i)/ myRebinnedTH1.GetBinWidth(i))
        myRebinnedDensityTH1.SetBinError(i, myRebinnedTH1.GetBinError(i)/ myRebinnedTH1.GetBinWidth(i))
        
        plotRegions = plotRegion.split(',')
        checkInRegions = [myRebinnedDensityTH1.GetXaxis().GetBinCenter(i)>w.var('mjj').getMin(reg) and myRebinnedDensityTH1.GetXaxis().GetBinCenter(i)<w.var('mjj').getMax(reg) for reg in plotRegions]      
        if not any(checkInRegions):
            myRebinnedDensityTH1.SetBinContent(i,0)
            myRebinnedDensityTH1.SetBinError(i,0)
    myRebinnedDensityTH1.GetXaxis().SetRangeUser(w.var('mjj').getMin(),w.var('mjj').getMax())
    #myRebinnedDensityTH1.GetXaxis().SetRangeUser(190.,w.var('mjj').getMax()) #edw X axis range top pad
    # paper:
    myRebinnedDensityTH1.GetYaxis().SetTitle('d#sigma/dm_{4#gamma} [pb/TeV]')
    # PAS:
    #myRebinnedDensityTH1.GetYaxis().SetTitle('d#sigma / dm_{jj} [pb / GeV]')
    myRebinnedDensityTH1.GetYaxis().SetTitleOffset(1)
    myRebinnedDensityTH1.GetYaxis().SetTitleSize(0.07)
    myRebinnedDensityTH1.GetYaxis().SetLabelSize(0.05)
    myRebinnedDensityTH1.GetXaxis().SetLabelOffset(1000)
    myRebinnedDensityTH1.Scale(0)
    myRebinnedDensityTH1.SetLineColor(rt.kWhite)
    myRebinnedDensityTH1.SetMarkerColor(rt.kWhite)
    myRebinnedDensityTH1.SetLineWidth(0)    
    #Plot mins and maxes
    myRebinnedDensityTH1.SetMaximum(20)#20
    myRebinnedDensityTH1.SetMinimum(5e-4)#2e-8
    myRebinnedDensityTH1.Draw("axis")
    
    if options.doTriggerFit or options.doSimultaneousFit or options.doSpectrumFit or options.noFit:
        #This is the one I'm drawing
        background.Draw("csame")

        #####################
        #Diphoton function
#        func = rt.TF1("func","[0]*(TMath::Power( (x/TMath::Sqrt(13000)), [1] + [2] * TMath::Log((x/TMath::Sqrt(13000))) + [3] * TMath::Power(TMath::Log((x/TMath::Sqrt(13    000))),2) + [4] * TMath::Power(TMath::Log((x/TMath::Sqrt(13000))),3)  )) ",300,3110);
#        #Parameters from bare root fit
#        func.FixParameter(0, 4.12175);
#        func.FixParameter(1, 1.50748);
#        func.FixParameter(2, -2.65006);
#        func.FixParameter(3,0);
#        func.FixParameter(4,0);
#        func.SetLineColor(rt.kBlue)
#        func.Draw("same")
        #####################

    else:
        h_background.SetLineColor(rt.kRed) #Tried
        h_background.SetLineWidth(2)
        h_background.Draw("histsame")


    g_signals = []
    for model, mass, xsec, signalFileName, sigHist, color, style in zip(models,masses,xsecs,signalFileNames,signalHistosRebin,colors,styles):        
        g_signal = rt.TGraphAsymmErrors(sigHist)
        g_signal.SetLineColor(color)
        g_signal.SetLineStyle(style)
        g_signal.SetLineWidth(3)

        lastX = 0
        lastY = 0
        firstX = 0
        firstY = 0
        notSet = True
        for i in range(0,g_signal.GetN()): 
            N = g_signal.GetY()[i]
            binWidth = g_signal.GetEXlow()[i] + g_signal.GetEXhigh()[i]      
            if g_signal.GetX()[i]>float(mass)*0.2 and notSet:   #was 0.75 edw signal             
                firstX = g_signal.GetX()[i]
                firstY = N/(binWidth * lumi)
                notSet = False
            
        for i in range(0,g_signal.GetN()):
            N = g_signal.GetY()[i]
            binWidth = g_signal.GetEXlow()[i] + g_signal.GetEXhigh()[i]            
            if g_signal.GetX()[i]<=float(mass)*0.2: #was 0.75 edw signal
                g_signal.SetPoint(i,firstX,firstY)
            else:
                g_signal.SetPoint(i, g_signal.GetX()[i], N/(binWidth * lumi))
            g_signal.SetPointEYlow(i, 0)
            g_signal.SetPointEYhigh(i, 0)            
            if g_signal.GetX()[i]>float(mass)*1.8:  #was 1.25 edw signal
                g_signal.SetPoint(i,lastX,lastY)
            else:                
                lastX = g_signal.GetX()[i]
                lastY = g_signal.GetY()[i]
        g_signals.append(g_signal)
        g_signal.Draw("cxsame")

    
    rt.gPad.SetLogy()
    
    l = rt.TLatex()
    l.SetTextAlign(11)
    l.SetTextSize(0.045)
    l.SetTextFont(42)
    l.SetNDC()
    #l.DrawLatex(0.7,0.96,"%i pb^{-1} (%i TeV)"%(lumi,w.var('sqrts').getVal()/1000.))
    #l.DrawLatex(0.72,0.96,"%.1f fb^{-1} (%i TeV)"%(lumi/1000.,w.var('sqrts').getVal()/1000.))
    l.DrawLatex(0.72,0.96,"%.1f fb^{-1} (%i TeV)"%(lumi,w.var('sqrts').getVal()/1000.))
    # PAS
    #l.SetTextFont(62)
    #l.SetTextSize(0.055)   
    #l.DrawLatex(0.2,0.96,"CMS")
    #l.SetTextFont(52)
    #l.SetTextSize(0.045)
    #l.DrawLatex(0.3,0.96,"Preliminary")
    # paper
    l.SetTextFont(62)
    l.SetTextSize(0.065)
    l.DrawLatex(0.22,0.89,"CMS")
    l.SetTextFont(52)
    l.SetTextSize(0.045)
    l.DrawLatex(0.32,0.89,"Preliminary")
        
    if options.signalFileName!=None:
        if 'Calo' in box:
            leg = rt.TLegend(0.58,0.58,0.89,0.94)
        else:
            leg = rt.TLegend(0.6,0.58,0.89,0.94)
    else:        
        leg = rt.TLegend(0.7,0.7,0.89,0.88)
    leg.SetTextFont(42)
    leg.SetFillColor(rt.kWhite)
    leg.SetFillStyle(0)
    leg.SetLineWidth(0)
    leg.SetLineColor(rt.kWhite)
    leg.AddEntry(g_data,"Data","pe")
    leg.AddEntry(background,"{} Fit".format(fitfunc),"l")
    for model, mass, xsec, signalFileName, g_signal in zip(models,masses,xsecs,signalFileNames, g_signals):
        if 'PF' in box:
            leg.AddEntry(g_signal,"%s (%.1f TeV)"%(model,float(mass)/1000.),"l")
        elif 'Calo' in box:
            if w.var('mjj').getMax() > 1246:
                leg.AddEntry(g_signal,"%s (%.1f TeV)"%(model,float(mass)/1000.),"l")
            else:    
                leg.AddEntry(g_signal,"%s (%.2f TeV)"%(model,float(mass)/1000.),"l")   
            #leg.AddEntry(None,"%.1f pb"%(float(xsec)),"")         
    leg.Draw()
    #background.Draw("csame")
    #g_data.Draw("pezsame")

    #pave_sel = rt.TPaveText(0.2,0.03,0.5,0.25,"NDC")
    pave_sel = rt.TPaveText(0.5,0.43,0.7,0.63,"NDC")
    pave_sel.SetFillColor(0)
    pave_sel.SetBorderSize(0)
    pave_sel.SetFillStyle(0)
    pave_sel.SetTextFont(42)
    pave_sel.SetTextSize(0.045)
    pave_sel.SetTextAlign(11)
    pave_sel.AddText("#chi^{{2}} / ndf = {0:.2f} / {1:d} = {2:.2f}".format(
                          list_chi2AndNdf_background[4], list_chi2AndNdf_background[5],
                          list_chi2AndNdf_background[4]/list_chi2AndNdf_background[5]))
    pave_sel.AddText("Prob. = {0:.2f}".format(rt.TMath.Prob(list_chi2AndNdf_background[4], list_chi2AndNdf_background[5])))
    #pave_sel.AddText(options.CUTSTRING)
    pave_sel.Draw("SAME")
    
    list_parameter = [p0_b, p0_b*(w.var('Ntot_%s_bkg'%box).getErrorHi() - w.var('Ntot_%s_bkg'%box).getErrorLo())/(2.0*w.var('Ntot_%s_bkg'%box).getVal()),                      
                      w.var('p1_%s'%box).getVal(), (w.var('p1_%s'%box).getErrorHi() - w.var('p1_%s'%box).getErrorLo())/2.0,
                      w.var('p2_%s'%box).getVal(), (w.var('p2_%s'%box).getErrorHi() - w.var('p2_%s'%box).getErrorLo())/2.0,
                      #w.var('pm3_%s'%box).getVal(), (w.var('pm3_%s'%box).getErrorHi() - w.var('pm3_%s'%box).getErrorLo())/2.0,
                      #w.var('pm4_%s'%box).getVal(), (w.var('pm4_%s'%box).getErrorHi() - w.var('pm4_%s'%box).getErrorLo())/2.0,
                      # w.var('p5_%s'%box).getVal(), (w.var('p5_%s'%box).getErrorHi() - w.var('_%s'%box).getErrorLo())/2.0,
                      w.var('meff_%s'%box).getVal(), (w.var('meff_%s'%box).getErrorHi() - w.var('meff_%s'%box).getErrorLo())/2.0,
                      w.var('seff_%s'%box).getVal(), (w.var('seff_%s'%box).getErrorHi() - w.var('seff_%s'%box).getErrorLo())/2.0]
# w.var('p3_%s'%box).getVal(), (w.var('p3_%s'%box).getErrorHi() - w.var('p3_%s'%box).getErrorLo())/2.0,


    pave_param = rt.TPaveText(0.55,0.03,0.9,0.25,"NDC")
    pave_param.SetTextFont(42)
    pave_param.SetFillColor(0)
    pave_param.SetBorderSize(0)
    pave_param.SetFillStyle(0)
    pave_param.SetTextAlign(11)
    pave_param.SetTextSize(0.045)
    pave_param.AddText("p_{0}"+" = {0:.2g} #pm {1:.2g}".format(list_parameter[0], list_parameter[1]))
    pave_param.AddText("p_{1}"+" = {0:.2f} #pm {1:.2f}".format(list_parameter[2], list_parameter[3]))
    pave_param.AddText("p_{2}"+" = {0:.2f} #pm {1:.2f}".format(list_parameter[4], list_parameter[5]))
    pave_param.AddText("p_{3}"+" = {0:.2f} #pm {1:.2f}".format(list_parameter[6], list_parameter[7]))
    if w.var('meff_%s'%box).getVal()>0 and w.var('seff_%s'%box).getVal()>0 and (options.doTriggerFit or options.doSimultaneousFit):
        pave_param.AddText("m_{eff}"+" = {0:.2f} #pm {1:.2f}".format(list_parameter[8], list_parameter[9]))
        pave_param.AddText("#sigma_{eff}"+" = {0:.2f} #pm {1:.2f}".format(list_parameter[10], list_parameter[11]))
    elif w.var('eff_bin%02d'%(0)) != None:
        effValList = []
        effErrHiList = []
        effErrLoList = []
        for i in range(0,len(x)-1):
            if not w.var('eff_bin%02d'%(i)).isConstant():
                effValList.append(w.var('eff_bin%02d'%(i)).getVal())
                effErrHiList.append(w.var('eff_bin%02d'%(i)).getErrorHi())
                effErrLoList.append(w.var('eff_bin%02d'%(i)).getErrorLo())

        valString = ",".join(["%.3f"%(effVal) for effVal in effValList])
        errString = ",".join(["^{%+.1e}_{%+.1e}"%(effErrHi,effErrLo) for effErrHi,effErrLo in zip(effErrHiList,effErrLoList)])
        pave_param.SetTextSize(0.025)
        pave_param.AddText("#epsilon = %s"%valString)
        pave_param.AddText("#delta#epsilon = %s"%errString)
            
    #pave_param.Draw("SAME")
    
    if options.doTriggerFit or options.doSimultaneousFit or options.doSpectrumFit or options.noFit:
        background.Draw("csame")
    else:
        h_background.SetLineColor(rt.kRed) #Tried
        h_background.SetLineWidth(2)
        h_background.Draw("histsame")
    g_data_clone.Draw("zpsame")
    g_data.Draw("zpsame")


    
    if 'PF' in box:
        # paper
        myRebinnedDensityTH1.GetYaxis().SetTitle('d#sigma/dm_{jj} [pb/TeV]')
        # PAS
        #myRebinnedDensityTH1.GetYaxis().SetTitle('d#sigma / dm_{jj} [pb / TeV]')
        myRebinnedDensityTH1.GetYaxis().SetLabelOffset(1000)
        yLab = rt.TLatex()
        yLab.SetTextAlign(32)
        yLab.SetTextSize(0.05)
        yLab.SetTextFont(42)
        xM = 0.
        yLab.DrawLatex(xM, 100, "10^{5}")
        yLab.DrawLatex(xM, 10, "10^{4}")
        yLab.DrawLatex(xM, 1, "10^{3}")
        yLab.DrawLatex(xM, 0.1, "10^{2}")
        yLab.DrawLatex(xM, 0.01, "10")
        yLab.DrawLatex(xM, 0.001, "1")
        yLab.DrawLatex(xM, 0.0001, "10^{#minus1}")
        yLab.DrawLatex(xM, 0.00001, "10^{#minus2}")
        yLab.DrawLatex(xM, 0.000001, "10^{#minus3}")
        yLab.DrawLatex(xM, 0.0000001, "10^{#minus4}")
        yLab.DrawLatex(xM, 0.00000001, "10^{#minus5}")
	yLab.DrawLatex(xM, 0.000000001, "10^{#minus6}")
	yLab.DrawLatex(xM, 0.0000000001, "10^{#minus7}")

        
        f_h2_log10_x_axis = rt.TF1("f_h2_log10_x_axis", "log10(x)", myRebinnedDensityTH1.GetXaxis().GetXmin(), myRebinnedDensityTH1.GetXaxis().GetXmax())
        b = rt.TGaxis(myRebinnedDensityTH1.GetXaxis().GetXmin(), 2e-8,
                      myRebinnedDensityTH1.GetXaxis().GetXmax(), 2e-8, "f_h2_log10_x_axis", 509, "BS", 0.0)
        b.SetTickSize(myRebinnedDensityTH1.GetTickLength("X"))
        b.SetMoreLogLabels()
        b.SetLabelOffset(1000)
        b.Draw()
        
        rt.gPad.Modified()
        rt.gPad.Update()
             
    if 'Calo' in box:
        # paper
        myRebinnedDensityTH1.GetYaxis().SetTitle('d#sigma/dm_{jj} [pb/TeV]')
        # PAS
        #myRebinnedDensityTH1.GetYaxis().SetTitle('d#sigma / dm_{jj} [pb / TeV]')
        myRebinnedDensityTH1.GetYaxis().SetLabelOffset(1000)
        yLab = rt.TLatex()
        yLab.SetTextAlign(32)
        yLab.SetTextSize(0.05)
        yLab.SetTextFont(42)
        xM = 434
        yLab.DrawLatex(xM, 1000, "10^{6}")
        yLab.DrawLatex(xM, 100, "10^{5}")
        yLab.DrawLatex(xM, 10, "10^{4}")
        yLab.DrawLatex(xM, 1, "10^{3}")
        yLab.DrawLatex(xM, 0.1, "10^{2}")
        yLab.DrawLatex(xM, 0.01, "10")
        yLab.DrawLatex(xM, 0.001, "1")
        yLab.DrawLatex(xM, 0.0001, "10^{#minus1}")


        
    pad_1.Update()

    pad_2.cd()
    
    h_fit_residual_vs_mass.GetXaxis().SetRangeUser(w.var('mjj').getMin(),w.var('mjj').getMax())
    #h_fit_residual_vs_mass.GetXaxis().SetRangeUser(190.,w.var('mjj').getMax()) #edw X axis range bottom pad
    h_fit_residual_vs_mass.GetYaxis().SetRangeUser(-3.5,3.5)
    h_fit_residual_vs_mass.GetYaxis().SetNdivisions(210,True)
    h_fit_residual_vs_mass.SetLineWidth(1)
    h_fit_residual_vs_mass.SetFillColor(rt.kRed)
    h_fit_residual_vs_mass.SetLineColor(rt.kBlack)
    
    h_fit_residual_vs_mass.GetYaxis().SetTitleSize(2*0.06)
    h_fit_residual_vs_mass.GetYaxis().SetLabelSize(2*0.05)
    # PAS
    #h_fit_residual_vs_mass.GetYaxis().SetTitleOffset(0.5)
    #h_fit_residual_vs_mass.GetYaxis().SetTitle('#frac{(Data-Fit)}{#sigma_{Data}}')
    # paper
    h_fit_residual_vs_mass.GetYaxis().SetTitleOffset(0.6)
    h_fit_residual_vs_mass.GetYaxis().SetTitle('#frac{(Data-Fit)}{Uncertainty}')
        
    h_fit_residual_vs_mass.GetXaxis().SetTitleSize(2*0.06)
    h_fit_residual_vs_mass.GetXaxis().SetLabelSize(2*0.05)
    #h_fit_residual_vs_mass.GetXaxis().SetTitle('m_{jj} [GeV]')
    # PAS
    #h_fit_residual_vs_mass.GetXaxis().SetTitle('Dijet Mass [GeV]')
    # paper
    h_fit_residual_vs_mass.GetXaxis().SetTitle('Average diphoton mass [TeV]')

    h_fit_residual_vs_mass.Draw("histsame")
    
    if 'PF' in box or w.var('mjj').getMax() > 1246:        
        # PAS
        #h_fit_residual_vs_mass.GetXaxis().SetTitle('Dijet Mass [TeV]')
        # paper
#       h_fit_residual_vs_mass.GetXaxis().SetTitle('Dijet mass [TeV]')
	h_fit_residual_vs_mass.GetXaxis().SetTitle('Average Dijet Mass [TeV]')
        h_fit_residual_vs_mass.GetXaxis().SetLabelOffset(1000)
        h_fit_residual_vs_mass.GetXaxis().SetNoExponent()
        h_fit_residual_vs_mass.GetXaxis().SetMoreLogLabels()    
        h_fit_residual_vs_mass.GetXaxis().SetNdivisions(999)
        xLab = rt.TLatex()
        xLab.SetTextAlign(22)
        xLab.SetTextFont(42)
        xLab.SetTextSize(2*0.05)	
        if w.var('mjj').getMin() < 1000:
            xLab.DrawLatex(600, -4, "0.6")
	    xLab.DrawLatex(800, -4, "0.8")	
            xLab.DrawLatex(1000, -4, "1")
	if w.var('mjj').getMin() < 200:
	    xLab.DrawLatex(200, -4, "0.2")
	if w.var('mjj').getMin() < 400:
	    xLab.DrawLatex(400, -4, "0.4")
	xLab.DrawLatex(1500, -4, "1.5")
        xLab.DrawLatex(2000, -4, "2")
        xLab.DrawLatex(3000, -4, "3")
        xLab.DrawLatex(4000, -4, "4")
        xLab.DrawLatex(5000, -4, "5")
        xLab.DrawLatex(6000, -4, "6")
        xLab.DrawLatex(7000, -4, "7")
        xLab.DrawLatex(8000, -4, "8")
        
        f_h2_log10_x_axis = rt.TF1("f_h2_log10_x_axis", "log10(x)", h_fit_residual_vs_mass.GetXaxis().GetXmin(), h_fit_residual_vs_mass.GetXaxis().GetXmax())
        a = rt.TGaxis(h_fit_residual_vs_mass.GetXaxis().GetXmin(), -3.5,
                      h_fit_residual_vs_mass.GetXaxis().GetXmax(), -3.5, "f_h2_log10_x_axis", 509, "BS", 0.0)
        a.SetTickSize(h_fit_residual_vs_mass.GetTickLength("X"))
        a.SetMoreLogLabels()
        a.SetLabelOffset(1000)
        a.Draw()
        
        rt.gPad.Modified()
        rt.gPad.Update()
    
    if 'Calo' in box:
        # PAS
        #h_fit_residual_vs_mass.GetXaxis().SetTitle('Dijet Mass [TeV]')
        # paper
        h_fit_residual_vs_mass.GetXaxis().SetTitle('Dijet mass [TeV]')
        h_fit_residual_vs_mass.GetXaxis().SetLabelOffset(1000)
        #h_fit_residual_vs_mass.GetXaxis().SetNoExponent()
        #h_fit_residual_vs_mass.GetXaxis().SetMoreLogLabels()    
        xLab = rt.TLatex()
        xLab.SetTextAlign(22)
        xLab.SetTextFont(42)
        xLab.SetTextSize(2*0.05)
        xLab.DrawLatex(600, -4, "0.6")
        xLab.DrawLatex(800, -4, "0.8")
        xLab.DrawLatex(1000, -4, "1")
        xLab.DrawLatex(1200, -4, "1.2")
        xLab.DrawLatex(1400, -4, "1.4")
        xLab.DrawLatex(1600, -4, "1.6")
        xLab.DrawLatex(1800, -4, "1.8")
        xLab.DrawLatex(2000, -4, "2")

    sigHistResiduals = []
    g_signal_residuals = []
    for model, mass, xsec, signalFileName, sigHist, color, style in zip(models,masses,xsecs,signalFileNames,signalHistosRebin,colors,styles):        
        sigHistResidual = sigHist.Clone(sigHist.GetName()+"_residual")
        sigHistResidual.SetLineColor(color)
        sigHistResidual.SetLineWidth(2)
        sigHistResidual.SetLineStyle(style)
        for bin in range (0,g_data.GetN()):
            value_data = g_data.GetY()[bin]
            err_tot_data = g_data.GetEYhigh()[bin]
            binWidth = g_data.GetEXlow()[i] + g_data.GetEXhigh()[i]
            value_signal = sigHist.GetBinContent(bin+1)/(binWidth*lumi)
        
            ## Signal residuals
            if err_tot_data>0:                
                sig_residual = (value_signal) / err_tot_data
            else:
                sig_residual = 0                                
    
            ## Fill histo with residuals
            sigHistResidual.SetBinContent(bin+1,sig_residual)
        sigHistResiduals.append(sigHistResidual)
        #sigHistResidual.Draw("histsame")
        g_signal_residual = rt.TGraphAsymmErrors(sigHistResidual)
        g_signal_residual.SetLineColor(color)
        g_signal_residual.SetLineWidth(3)
        g_signal_residual.SetLineStyle(style)

        lastX = 0
        lastY = 0
        firstX = 0
        firstY = 0
        notSet = True
        for i in range(0,g_signal_residual.GetN()): 
            N = g_signal_residual.GetY()[i]
            binWidth = g_signal_residual.GetEXlow()[i] + g_signal_residual.GetEXhigh()[i]      
            if g_signal_residual.GetX()[i]>float(mass)*0.2 and notSet:  #edw signal              
                firstX = g_signal_residual.GetX()[i]
                firstY = N
                notSet = False
            
        for i in range(0,g_signal_residual.GetN()):
            N = g_signal_residual.GetY()[i]
            binWidth = g_signal_residual.GetEXlow()[i] + g_signal_residual.GetEXhigh()[i]            
            if g_signal_residual.GetX()[i]<=float(mass)*0.2:  #edw signal
                g_signal_residual.SetPoint(i,firstX,firstY)
            else:
                g_signal_residual.SetPoint(i, g_signal_residual.GetX()[i], N)
            g_signal_residual.SetPointEYlow(i, 0)
            g_signal_residual.SetPointEYhigh(i, 0)            
            if g_signal_residual.GetX()[i]>float(mass)*1.8:  #edw signal
                g_signal_residual.SetPoint(i,lastX,lastY)
            else:                
                lastX = g_signal_residual.GetX()[i]
                lastY = g_signal_residual.GetY()[i]
        g_signal_residuals.append(g_signal_residual)
        g_signal_residual.Draw("cxsame")

        
    #c.RedrawAxis() # request from David

    #Plot 1D distribution of pulls
    #c_pulls_distribution = rt.TCanvas()
    #c_pulls_distribution.cd()
    #rt.gStyle.SetOptStat(1)
    #h_pulls_distribution = rt.TH1D("h_pulls_distribution","", 28,-3.5,3.5)
    #for i in range(1,h_fit_residual_vs_mass.GetNbinsX()+1):
    #	if (h_fit_residual_vs_mass.GetBinContent(i)>0 or h_fit_residual_vs_mass.GetBinContent(i)<-0.001):
    #	pull_value = h_fit_residual_vs_mass.GetBinContent(i)
    #	h_pulls_distribution.Fill(pull_value)
    #h_pulls_distribution.GetYaxis().SetTitle("Entries")
    #h_pulls_distribution.GetXaxis().SetTitle("Pulls")
    #h_pulls_distribution.SetMarkerStyle(8)
    #h_pulls_distribution.SetMarkerColor(rt.kBlue)
    #h_pulls_distribution.SetMarkerSize(0.5)
    #h_pulls_distribution.Draw()
    #h_pulls_distribution.Fit('gaus')
    #rt.gStyle.SetOptFit(1111)
    #rt.gStyle.SetOptStat(0)

    #c_pulls_distribution.Print(options.outDir+"/Pulls_mjj_%s_%s.png"%(fitRegion.replace(',','_'),box))
    c.Print(options.outDir+"/fit_mjj_%s_%s_%s.png"%(fitRegion.replace(',','_'),box,year))
    c.Print(options.outDir+"/fit_mjj_%s_%s_%s.C"%(fitRegion.replace(',','_'),box,year))
    #c.Print(options.outDir+"/SB_fit_mjj_%s_%s.png"%(fitRegion.replace(',','_'),box))	#for sb fit
    #c.Print(options.outDir+"/SB_fit_mjj_%s_%s.C"%(fitRegion.replace(',','_'),box))
    tdirectory.cd()
    c.Write()
    #c_pulls_distribution.Write()

    outFileName = "DijetFitResults_%s_%s.root"%(box,year)
    #outFileName = "DijetFitResults_sb_%s.root"%(box)	#for sb fit
    outFile = rt.TFile(options.outDir+"/"+outFileName,'recreate')
    outFile.cd()
    w.Write()
    outFile.Close()
