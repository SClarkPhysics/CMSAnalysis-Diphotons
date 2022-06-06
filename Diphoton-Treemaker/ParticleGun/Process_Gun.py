import os 
import sys

#sys.path.append("../")

import Treemaker_ParticleGun
#import ProcessPileup
#import CopyPileup

#GunList = ["aGun_flat2"]
GunList = ["aGun_flat3"]

for sig in GunList:
  Treemaker_ParticleGun.Treemaker("/cms/sclark-2/RUCLU_Outputs/ParticleGun/{}/".format(sig), sig, False)
  #ProcessPileup.ProcessPileup("/cms/xaas-2/DiPhotonsTrees/{}_{}.root".format(sig,year))
  #CopyPileup.CopyPileup("/cms/xaastorage-2/DiPhotonsTrees/{}_{}.root".format(sig,year))
  #os.remove("{}_{}.root".format(sig,year))
