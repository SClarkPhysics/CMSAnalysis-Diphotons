import os 
import sys

#sys.path.append("../")

import Treemaker_ParticleGun
#import ProcessPileup
#import CopyPileup

HTList = ["HT100To200",
          "HT200To400"]

for sig in HTList:
  Treemaker_ParticleGun.Treemaker("/cms/sclark-2/RUCLU_Outputs/GJets/2016/{}/".format(sig), sig, False)
  #ProcessPileup.ProcessPileup("/cms/xaas-2/DiPhotonsTrees/{}_{}.root".format(sig,year))
  #CopyPileup.CopyPileup("/cms/xaastorage-2/DiPhotonsTrees/{}_{}.root".format(sig,year))
  #os.remove("{}_{}.root".format(sig,year))
