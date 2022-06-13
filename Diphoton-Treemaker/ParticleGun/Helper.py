import os
dir_path = os.path.dirname(os.path.realpath(__file__)) #Get directory where this Treemaker.py is located


keeplist = ['lumiSec','run','id', 
            "weight",
            #"pvtx_size",
            #"HLT_DoublePhoton", "HLT_EleTrig",
            "clu1_pt",
            "clu1_eta",
            "clu1_phi",
            "clu1_energy",
            "clu1_moe",
            "clu1_iso",
            "clu1_monopho",
            "clu1_dipho",
            "clu1_hadron",
            "clu2_pt",
            "clu2_eta",
            "clu2_phi",
            "clu2_energy",
            "clu2_moe",
            "clu2_iso",
            "clu2_monopho",
            "clu2_dipho",
            "clu2_hadron",
            'masym', 'deta','aM', 'XM', 'alpha']

def MakeFolder(N):
    import os
    if not os.path.exists(N):
     os.makedirs(N)

