#Input: txt file from SCurve
#Output: Root file with which channels never fire, and their corresponding VFAT.

import ROOT
from argparse import RawTextHelpFormatter
import argparse
import os
import pathlib
import uproot
import numpy as np
import time
import shutil

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
    with args.ifile as _file:
        ds=np.loadtxt(_file,delimiter=',',skiprows=1)
        deadvfats=np.array([])
        deadchannels=np.array([])
        for h in np.unique(ds[:,0]):
            ii=np.where(ds[:,0]==h)
            sortedbyvfatch=([])
            sortedbyvfathit=([])
            for i in ii:
                sortedbyvfatch=np.append(sortedbyvfatch,ds[i,1])
                sortedbyvfathit=np.append(sortedbyvfathit,ds[i,3])
            for g in np.unique(sortedbyvfatch):
                jj=np.where(sortedbyvfatch==g)
                sortedbychhit=([])
                for j in jj:
                    sortedbychhit=np.append(sortedbychhit,sortedbyvfathit[j])
                if np.sum(sortedbychhit)==0:
                    deadvfats=np.append(deadvfats,h)
                    deadchannels=np.append(deadchannels,int(g))
        print(deadvfats,'and',deadchannels)
        with uproot.recreate("outputfile.root") as f:
            t=f.mktree("Output",{"VFAT":int,"Channel":int})
            t.extend({"VFAT":deadvfats,"Channel":deadchannels})

if __name__=='__main__': main()
