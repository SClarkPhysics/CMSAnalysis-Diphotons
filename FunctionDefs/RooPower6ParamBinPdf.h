//---------------------------------------------------------------------------
#ifndef HiggsAnalysis_CombinedLimit_RooPower6ParamBinPdf_h
#define HiggsAnalysis_CombinedLimit_RooPower6ParamBinPdf_h
//---------------------------------------------------------------------------
#include "RooAbsPdf.h"
#include "RooConstVar.h"
#include "RooRealProxy.h"
//---------------------------------------------------------------------------
class RooRealVar;
class RooAbsReal;

#include "Riostream.h"
#include "TMath.h"
#include <TH1.h>
#include "Math/SpecFuncMathCore.h"
#include "Math/SpecFuncMathMore.h"
#include "Math/Functor.h"
#include "Math/WrappedFunction.h"
#include "Math/IFunction.h"
#include "Math/Integrator.h"

//---------------------------------------------------------------------------
class RooPower6ParamBinPdf : public RooAbsPdf
{
public:
   RooPower6ParamBinPdf() {} ;
   RooPower6ParamBinPdf(const char *name, const char *title,
		    RooAbsReal& _th1x, RooAbsReal& _p1,
		    RooAbsReal& _p2, RooAbsReal& _p3, RooAbsReal& _p4, RooAbsReal& _p5,
		    RooAbsReal& _sqrts, RooAbsReal& _meff, RooAbsReal& _seff);
   RooPower6ParamBinPdf(const char *name, const char *title,
		    RooAbsReal& _th1x, RooAbsReal& _p1,
		    RooAbsReal& _p2, RooAbsReal& _p3, RooAbsReal& _p4, RooAbsReal& _p5,
		    RooAbsReal& _sqrts);
   RooPower6ParamBinPdf(const RooPower6ParamBinPdf& other,
      const char* name = 0);
   void setTH1Binning(TH1* _Hnominal);
   void setAbsTol(double _absTol);
   void setRelTol(double _relTol);
   virtual TObject* clone(const char* newname) const { return new RooPower6ParamBinPdf(*this,newname); }
   inline virtual ~RooPower6ParamBinPdf() { }

   Int_t getAnalyticalIntegral(RooArgSet& allVars, RooArgSet& analVars, const char* rangeName=0) const;
   Double_t analyticalIntegral(Int_t code, const char* rangeName=0) const;

protected:   

   RooRealProxy th1x;        // dependent variable
   RooRealProxy p1;       // p1
   RooRealProxy p2;        // p2
   RooRealProxy p3;        // p3
   RooRealProxy p4;        // p4
   RooRealProxy p5;        // p5
   RooRealProxy sqrts;        // sqrts
   RooRealProxy meff;        // meff
   RooRealProxy seff;        // seff
   Int_t xBins;        // X bins
   Double_t xArray[2000]; // xArray[xBins+1]
   Double_t xMax;        // X max
   Double_t xMin;        // X min
   Double_t relTol;      //relative tolerance for numerical integration
   Double_t absTol;      //absolute tolerance for numerical integration

   Double_t evaluate() const;
private:
   ClassDef(RooPower6ParamBinPdf,1) // RazorPower6ParamBinPdf function
    
};
//---------------------------------------------------------------------------
#endif

#include "Math/IFunction.h"
#include "Math/IParamFunction.h"
 
class Power6ParamFunction: public ROOT::Math::IParametricFunctionOneDim
{
private:
   const double *pars;
 
public:
   double DoEvalPar(double x,const double* p) const
   {
     double pdf = p[0]*pow(p[2] + p[3]*x + p[4]*x*x + p[5]*x*x*x, p[1]);
     double eff = 1.;
     //if (p[6]>0) eff = 0.5 * (1.0 + TMath::Erf((x - p[5])/p[6])) ; // Error function
     if (p[7]>0) eff = 1.0/(1.0 + exp(-2.4*(x - p[6])/p[7])) ; // Sigmoid function
     return pdf*eff;
   }
   
   double DoEval(double x) const
   {
     double pdf = pars[0]*pow(pars[2] + pars[3]*x + pars[4]*x*x + pars[5]*x*x*x, pars[1]);
     double eff = 1.;
     //if (pars[6]>0) eff = 0.5 * (1.0 + TMath::Erf((x - pars[5])/pars[6])); // Error function     
     if (pars[7]>0) eff = 1.0/(1.0 + exp(-2.4*(x - pars[6])/pars[7])); // Sigmoid function
     return pdf*eff;
   }
 
   ROOT::Math::IBaseFunctionOneDim* Clone() const
   {
      return new Power6ParamFunction();
   }
 
   const double* Parameters() const
   {
      return pars;
   }
 
   void SetParameters(const double* p)
   {
      pars = p;
   }
 
   unsigned int NPar() const
   {
      return 8;
   }
};
