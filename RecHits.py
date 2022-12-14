#Identifies clusters within each EVT trigger and assigns coordinate position to each
#Returns root file (outputfile.root) with Event Number, OH#, VFAT#, eta partition, lowest strip# of cluster, and phi coordinate

import ROOT
from argparse import RawTextHelpFormatter
import argparse
import os
import pathlib
import uproot
import uproot3
import numpy as np
import awkward as ak
import matplotlib.pyplot as plt
import time
import shutil
import scipy
from scipy import stats
from collections import Counter
ROOT.gROOT.SetBatch(True)

parser = argparse.ArgumentParser(
    description='''Scripts that: \n\t-Parses the output of https://github.com/antonellopellecchia/testbeam-analysis/blob/feature/may2022/unpacker.cc\n\t-For each VFATs, plots number of hits vs  latency ''',
    epilog="""Typical exectuion\n\t python3 latency_analyzer.py  ./inoutfile.root  outdir """,
    formatter_class=RawTextHelpFormatter
)

parser.add_argument("ifile", type=pathlib.Path, help="Input file")
parser.add_argument('odir', type=pathlib.Path, help="Output directory")
parser.add_argument("-v", "--verbose", action="store_true", help="Activate logging")
parser.add_argument("-n", "--events", type=int, default=-1, help="Number of events to analyse")

args = parser.parse_args()
inputfile=str(args.ifile)
timestamp = inputfile.split(".root")[-2].split("/")[-1] if "run" in inputfile else time.strftime("%-y%m%d_%H%M")
outdir = args.odir / timestamp 


def main():
    os.makedirs(outdir, exist_ok=True)
    RecHitArray=np.array([])
    EvtNumArray=np.array([])
    ClusterLengthArray=np.array([])
    OHArray=np.array([])
    VFATArray=np.array([])
    etaArray=np.array([])
    stripArray=np.array([])
    phiArray=np.array([])
    with uproot.open(args.ifile) as _file:
        tree = _file["outputtree"]
        nhits = tree["nhits"].array(entry_stop=args.events)
        latencies = tree["latency"].array(entry_stop=args.events)
        pulse_stretches = tree["pulse_stretch"].array(entry_stop=args.events)
        slots = tree["slot"].array(entry_stop=args.events)
        VFATs =  tree["VFAT"].array(entry_stop=args.events)
        OHs =  tree["OH"].array(entry_stop=args.events)
        CHs = tree["CH"].array(entry_stop=args.events)
        Chambers = tree["digiChamber"].array(entry_stop=args.events)
        etas = tree["digiEta"].array(entry_stop=args.events)
        strips = tree["digiStrip"].array(entry_stop=args.events)
        rechitindex=0
        n_triggers = len(latencies)
        hit=0
        clustersizelist=np.array([])
        RecInfoList=list() #Attempt to get Evt# - hit lengths    ### RecInfoList formerly doubletestlist
        for evt_num,lat in enumerate(latencies):
            oldindex=0
            evtentry=list()
            evtentry.append(evt_num)
            clustersizelist3=np.array([])
            striplist=np.array([])
            VFATlist=np.array([])
            etalist=np.array([])
            for o in np.unique(OHs[evt_num]):
                oo=np.where(OHs[evt_num]==o)[0]
                sortedbyOHVFs=np.array([])
                sortedbyOHetas=np.array([])
                sortedbyOHstrips=np.array([])
                for i in oo:
                    sortedbyOHVFs=np.append(sortedbyOHVFs,VFATs[evt_num][i])
                    sortedbyOHetas=np.append(sortedbyOHetas,etas[evt_num][i])
                    sortedbyOHstrips=np.append(sortedbyOHstrips,strips[evt_num][i])
                for j in np.unique(sortedbyOHVFs):
                    jj=np.where(sortedbyOHVFs==j)[0]
                    sortedbyVFstrips=np.array([])
                    sortedbyVFetas=np.array([])
                    for k in jj:
                        sortedbyVFetas=np.append(sortedbyVFetas,sortedbyOHetas[k])
                        sortedbyVFstrips=np.append(sortedbyVFstrips,sortedbyOHstrips[k])
                    for l in np.unique(sortedbyVFetas):
                        ll=np.where(sortedbyVFetas==l)[0]
                        sortedbyetaetas=np.array([])
                        sortedbyetastrips=np.array([])
                        for m in ll:
                            sortedbyetaetas=np.append(sortedbyetaetas,sortedbyVFetas[m])
                            sortedbyetastrips=np.append(sortedbyetastrips,sortedbyVFstrips[m])
                        finalsortstrips=ak.sort(sortedbyetastrips)
                        count=0
                        countlist=[0]
                        for c in range(len(finalsortstrips)-1):
                            count+=1
                            if len(finalsortstrips)==1:
                                RecHitArray=np.append(RecHitArray,int(rechitindex))
                                EvtNumArray=np.append(EvtNumArray,int(evt_num))
                                ClusterLengthArray=np.append(ClusterLengthArray,int(1))
                                OHArray=np.append(OHArray,int(o))
                                VFATArray=np.append(VFATArray,int(j))
                                etaArray=np.append(etaArray,int(l))
                                stripArray=np.append(stripArray,int(finalsortstrips[0]))
                                phiArray=np.append(phiArray,finalsortstrips[0]*np.pi/(18*6*64))
                                print("This was used")
                                rechitindex+=1
                            elif finalsortstrips[c]!=finalsortstrips[c+1]-1:
                                countlist.append(count)
                                RecHitArray=np.append(RecHitArray,int(rechitindex))
                                EvtNumArray=np.append(EvtNumArray,int(evt_num))
                                ClusterLengthArray=np.append(ClusterLengthArray,int(count))
                                OHArray=np.append(OHArray,int(o))
                                VFATArray=np.append(VFATArray,int(j))
                                etaArray=np.append(etaArray,int(l))
                                stripArray=np.append(stripArray,int(finalsortstrips[np.sum(countlist)-count]))
                                phiArray=np.append(phiArray,((finalsortstrips[np.sum(countlist)-count]+finalsortstrips[np.sum(countlist)])/2)*(np.pi/(6*64*18)))
                                count=0
                                rechitindex+=1
                        if len(finalsortstrips)>0:
                            RecHitArray=np.append(RecHitArray,int(rechitindex))
                            EvtNumArray=np.append(EvtNumArray,int(evt_num))
                            ClusterLengthArray=np.append(ClusterLengthArray,int(count+1))
                            OHArray=np.append(OHArray,int(o))
                            VFATArray=np.append(VFATArray,int(j))
                            etaArray=np.append(etaArray,int(l))
                            stripArray=np.append(stripArray,int(finalsortstrips[len(finalsortstrips)-count-1]))
                            phiArray=np.append(phiArray,((finalsortstrips[len(finalsortstrips)-count-1]+finalsortstrips[len(finalsortstrips)-1])/2)*(np.pi/(6*64*18)))
                            #phiArray takes mean strip value of a cluster, and converts to radians. 6*64 channels per chamber, 18 chambers in installation
                            rechitindex+=1

    with uproot.recreate("outputfile.root") as f:
        t=f.mktree("Output",{"RecHit":int,"Evt_Num":int,"ClusterLength":int,"OH":int,"VFAT":int,"eta":int,"strip":int,"phicoord":np.float64})
        t.extend({"RecHit": RecHitArray, "Evt_Num": EvtNumArray,"ClusterLength":ClusterLengthArray,"OH":OHArray,"VFAT":VFATArray,"eta":etaArray,"strip":stripArray,"phicoord":phiArray})

if __name__=='__main__': main()
