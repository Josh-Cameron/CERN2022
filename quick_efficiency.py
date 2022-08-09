#Gives [number of evts where specified VFATs fire]/[Number of evts triggered by coincident scintillators]
#Specified VFATs should have scintillators on either side
#VFATs of Interest defined on line 39
#Error bars given by Clopper-Pearson Interval


import ROOT
from argparse import RawTextHelpFormatter
import argparse
import os
import pathlib
import uproot
import numpy as np
import awkward as ak
import matplotlib.pyplot as plt
import time
import shutil
import scipy
from scipy import stats

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

VFATsofInterest=[0,2] #####USER DEFINED
def main():
    os.makedirs(outdir, exist_ok=True)
    
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

        n_triggers = len(latencies)
        hit=0
        for evt_num,lat in enumerate(latencies):
#            print(f"{evt_num}\t{lat}\t{VFATs[evt_num]}")
            if any(x in VFATs[evt_num] for x in VFATsofInterest):
                hit=hit+1;
#               print("SOMETHING HIT")
        a=.05
        low=scipy.stats.beta.ppf(a/2,hit,n_triggers-hit+1)
        high=scipy.stats.beta.ppf(1-a/2,hit+1,n_triggers-hit)
        print("Number of hits:",hit)
        print("Number of events:",n_triggers)
        print("Efficiency:", hit/n_triggers)
        print("Uncertainty Interval is",[low,high],"with alpha=",a)

if __name__=='__main__': main()
