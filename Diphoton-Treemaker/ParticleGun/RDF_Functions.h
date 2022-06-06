// Kinematic variables for RDF
#include <vector>
#include <stdexcept>
#include <string>
#include <algorithm>
#include <iostream>
#include <cmath>
#include "ROOT/RVec.hxx"

using namespace std;
using namespace ROOT::VecOps;
using rvec_f = const RVec<float> &;
using rvec_u = const RVec<unsigned int> &;

int getN(rvec_f ds){
  return ds.size();
}


//RVec<unsigned long> indexes(rvec_f DS)
RVec<unsigned int> indexes(rvec_f DS)
	{
		unsigned int I1 = 0, I2 = 0;
		float S1 = 0., S2 = 0.;
		for (int i = 0; i<DS.size(); ++i)
		{
			if (DS[i] > S1) {I1 = i; S1 = DS[i];}
		}
		for (int i = 0; i<DS.size(); ++i)
		{
			if (DS[i] > S2) {if (i!=I1) {I2 = i; S2 = DS[i];}}
		}
		using s = typename RVec<unsigned int>::size_type;
		RVec<unsigned int> O((s)2);
		O[0] = I1; O[1] = I2;
		return O;
	}

float get_Deta(unsigned int I1, unsigned int I2, rvec_f eta)
    {
		if (I1 != I2)
		{
			return abs(eta[I1] - eta[I2]);
		}
		else return -1.0;
    }

float get_Masym(unsigned int I1, unsigned int I2, rvec_f moe, rvec_f E)
    {
		if (I1 != I2)
		{
			float m1 = moe[I1]*E[I1];
			float m2 = moe[I2]*E[I2];
			return abs(m1-m2)/(m1+m2);
		}
		else return -1.0;
    }
    
int getSign(float num){
  if(num < 0){return -1.;}
  else{return 1;}
}
 
float get_aM(unsigned int I1, unsigned int I2, rvec_f moe, rvec_f E)
    {
		if (I1 != I2)
		{
			float m1 = moe[I1]*E[I1];
			float m2 = moe[I2]*E[I2];
			return (m1+m2)/2.0;
		}
		else return -1.0;
    }
    
float ZShift(float eta, float zPV)
	{
	  float R = 129.;
	  float theta = 2.*TMath::ATan(TMath::Exp(-1.*abs(eta)));
	  float z = R / TMath::Tan(theta) * getSign(eta);
	  float zp;
	  float thetaprime;
	  float etaprime = 0.;
	  if (zPV < 0 && z >= 0){
		  zp = abs(zPV) + abs(z);
		  thetaprime = TMath::ATan(R/zp);
		  etaprime = -1. * TMath::Log(TMath::Tan(thetaprime/2.));
		  return etaprime;
	  }
	  if (zPV >= 0 && z < 0){
		  zp = abs(zPV) + abs(z);
		  thetaprime = TMath::ATan(R/zp);
		  etaprime = TMath::Log(TMath::Tan(thetaprime/2.));
		  return etaprime;
	  }

	  if (zPV >= 0 && z >= 0 && z > zPV){
		  zp = abs(z) - abs(zPV);
		  thetaprime = TMath::ATan(R/zp);
		  etaprime = -1. * TMath::Log(TMath::Tan(thetaprime/2.));
		  return etaprime;
	  }
	  if (zPV < 0 && z < 0 && z < zPV){
		  zp = abs(z) - abs(zPV);
		  thetaprime = TMath::ATan(R/zp);
		  etaprime = TMath::Log(TMath::Tan(thetaprime/2.));
		  return etaprime;
	  }

	  if (zPV >= 0 && z >= 0 && z < zPV){
		  zp = abs(zPV) - abs(z);
		  thetaprime = TMath::ATan(R/zp);
		  etaprime = TMath::Log(TMath::Tan(thetaprime/2.));
		  return etaprime;
	  }
	  if (zPV < 0 && z < 0 && z >= zPV){
		  zp = abs(zPV) - abs(z);
		  thetaprime = TMath::ATan(R/zp);
		  etaprime = -1.*TMath::Log(TMath::Tan(thetaprime/2.));
		  return etaprime;
	  }
	  return etaprime;
	}

RVec<float> get_pT(rvec_f moe, rvec_f E, rvec_f eta, rvec_f phi, rvec_f zpv, float sf)
{
  RVec<float> Es;

  for(unsigned int ii=0; ii< moe.size(); ii++){
    
    float m1 = moe[ii]*E[ii];
    float pt = E[ii] * TMath::Sin(TMath::ATan(TMath::Exp(-1*ZShift( eta[ii], zpv[0] ) ) ) * 2 );

	  ROOT::Math::PtEtaPhiEVector v1(pt,eta[ii],phi[ii],E[ii]);
    v1 = sf*v1;
    Es.push_back(v1.Pt());

  }
  return Es;
}
	
float get_XM(unsigned int I1, unsigned int I2, rvec_f moe, rvec_f E, rvec_f eta, rvec_f phi, rvec_f zpv, rvec_f pT)
    {
		if (I1 != I2)
		{
			float m1 = moe[I1]*E[I1];
			float m2 = moe[I2]*E[I2];
			//float pt1 = E[I1] * TMath::Sin(TMath::ATan(TMath::Exp(-1*ZShift( eta[I1], zpv[0] ) ) ) * 2 );
			//float pt2 = E[I2] * TMath::Sin(TMath::ATan(TMath::Exp(-1*ZShift( eta[I2], zpv[0] ) ) ) * 2 );
			float pt1 = pT[I1];
			float pt2 = pT[I2];
			ROOT::Math::PtEtaPhiMVector v1(pt1,eta[I1],phi[I1],m1);
			ROOT::Math::PtEtaPhiMVector v2(pt2,eta[I2],phi[I2],m2);

			return (v1+v2).M();
		}
		else return -1.0;
    }

RVec<float> get_match_DR(rvec_f base_pt, rvec_f base_eta, rvec_f base_phi, rvec_f base_energy, rvec_f match_pt, rvec_f match_eta, rvec_f match_phi, rvec_f match_energy)
{

  RVec<float> DRs;
  
  //Loop through Clusters
  for(unsigned int cc=0; cc<base_eta.size(); cc++){ 
    
    TLorentzVector base;
    base.SetPtEtaPhiE(base_pt.at(cc), base_eta.at(cc), base_phi.at(cc), base_energy.at(cc) );

    float minDr = 999.;

    //Loop through photons
    for(unsigned int pp=0; pp<match_eta.size(); pp++){ 
      TLorentzVector match;
      match.SetPtEtaPhiE(match_pt.at(pp), match_eta.at(pp), match_phi.at(pp), match_energy.at(pp) );
        if(base.DeltaR(match) < minDr){
          minDr = base.DeltaR(match);
        }
      }
    DRs.push_back(std::forward<float>(minDr));
  }
  return DRs;
}

RVec<int> get_match_index(rvec_f base_pt, rvec_f base_eta, rvec_f base_phi, rvec_f base_energy, rvec_f match_pt, rvec_f match_eta, rvec_f match_phi, rvec_f match_energy)
{
  RVec<int> indexes;
  
  //Loop through Clusters
  for(unsigned int cc=0; cc<base_eta.size(); cc++){ 
    
    TLorentzVector base;
    base.SetPtEtaPhiE(base_pt.at(cc), base_eta.at(cc), base_phi.at(cc), base_energy.at(cc) );

    float minDr = 999.;
    int closestIdx = -999;

    //Loop through photons
    for(unsigned int pp=0; pp<match_eta.size(); pp++){ 
      TLorentzVector match;
      match.SetPtEtaPhiE(match_pt.at(pp), match_eta.at(pp), match_phi.at(pp), match_energy.at(pp) );
        if(base.DeltaR(match) < minDr){
          minDr = base.DeltaR(match);
          closestIdx = pp;
        }
      }
    indexes.push_back(std::forward<int>(closestIdx));
  }
  return indexes;
}

RVec<float> get_match_param(rvec_f param, rvec_f base_pt, rvec_f base_eta, rvec_f base_phi, rvec_f base_energy, rvec_f match_pt, rvec_f match_eta, rvec_f match_phi, rvec_f match_energy)
{
  RVec<float> params;

  //Loop through Clusters
  for(unsigned int cc=0; cc<base_eta.size(); cc++){ 
    
    TLorentzVector base;
    base.SetPtEtaPhiE(base_pt.at(cc), base_eta.at(cc), base_phi.at(cc), base_energy.at(cc) );

    float minDr = 999.;
    int closestIdx = -999;

    //Loop through photons
    for(unsigned int pp=0; pp<match_eta.size(); pp++){ 
      TLorentzVector match;
      match.SetPtEtaPhiE(match_pt.at(pp), match_eta.at(pp), match_phi.at(pp), match_energy.at(pp) );
        if(base.DeltaR(match) < minDr){
          minDr = base.DeltaR(match);
          closestIdx = pp;
        }
      }
	float P = param.at(closestIdx);
    params.push_back(std::forward<float>(P));
  }
  return params;
}

RVec<float> get_param(rvec_f idxs, rvec_f param) 
{
  RVec<float> params;

  //Loop through Clusters
  for(unsigned int cc=0; cc<idxs.size(); cc++){ 
	float P = param.at(idxs.at(cc));
    params.push_back( std::forward<float>(P));
  }
  return params;
}

RVec<float> get_JetE(rvec_f idxs, rvec_f DR, rvec_f jetE, rvec_f rucluE) 
{
  RVec<float> params;
  for(unsigned int cc=0; cc<idxs.size(); cc++){ 
    //if(idxs.at(cc)<0){ params.push_back(rucluE.at(cc)); } //No jet, get Ruclu energy
    if(DR.at(cc)>0.15){
		float P = rucluE.at(cc);
		params.push_back(std::forward<float>(P));
		} //Not near a jet, get ruclu e
    else{
		float P = jetE.at( idxs.at(cc) );
		params.push_back( std::forward<float>(P) );
		} //Near jet, get the actual jet Energy
  }
  return params;
}
