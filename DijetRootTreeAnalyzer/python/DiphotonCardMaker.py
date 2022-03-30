import os
import sys

def RunDataCardMaker(o):
    config = " -c config/diphoton_%s" % (str(o.FIT))+".config"
    lumi = " --lumi " + str(int(float(o.LUM)*1000.))
    box = " -b diphoton"#_" + str(o.SIG)
    if o.FIT != "combine": box += "_%s" % str(o.FIT)
    mass = " --mass " + str(o.SIG).split("X")[1].split("A")[0]
    output = " -d output"
    xs = " --xsec 1."
    inputs = " -i output/DijetFitResults_diphoton_envelope.root"
    inputs += " inputs/" + str(o.SIG) + "/PLOTS_" + str(o.SIG) + ".root"
    inputs += " inputs/"+ str(o.SIG)+"/Sig_nominal.root"
    jesup = " --jesUp inputs/"+ str(o.SIG)+"/Sig_SU.root"
    jesdown = " --jesDown inputs/"+ str(o.SIG)+"/Sig_SD.root"
    jerup = " --jerUp inputs/"+ str(o.SIG)+"/Sig_PU.root"
    jerdown = " --jerDown inputs/"+ str(o.SIG)+"/Sig_PD.root"

            

    dcstring = "python python/WriteDataCard_4J_envelope_Jim.py" + config + mass + box + output + inputs + jesup + jesdown + jerup + jerdown + xs + lumi + " --multi"
    print(dcstring)
    os.system(dcstring)

if __name__ == "__main__":
    from optparse import OptionParser
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--fit", dest="FIT", type=str, help="name of fit function", metavar="FITFUNC")
    parser.add_option("-l", "--lumi", dest="LUM", type=str, help="lumi in this sample (in fb-1)", metavar="THELUMI")
    parser.add_option("-s", "--sig", dest="SIG", type=str, help="signal samples", metavar="THESIGNAL")
    (o, args) = parser.parse_args()
    RunDataCardMaker(o)