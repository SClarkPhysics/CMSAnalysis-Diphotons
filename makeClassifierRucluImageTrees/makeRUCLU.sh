#!/bin/bash

cd /cms/sclark/rucluMaker_ForImages/CMSSW_10_6_14/src/ml_photons_cmssw/ml_photons/python/cluster_general/
./call.sh $1 $2 $3 $4 $5
mv outflat.root /cms/sclark/DiphotonAnalysis/CMSSW_11_1_0_pre7/src/CMSAnalysis-Diphotons/makeClassifierRucluImageTrees/.
cd /cms/sclark/DiphotonAnalysis/CMSSW_11_1_0_pre7/src/CMSAnalysis-Diphotons/makeClassifierRucluImageTrees
cmsenv
