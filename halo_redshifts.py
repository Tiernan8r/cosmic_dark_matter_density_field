#!/usr/bin/env python
import os
import pickle
import sys

halo_types = ["rockstar", "groups", "snapshots"]

if len(sys.argv) < 3:
    print("Need halo type and dataset name input!")
    sys.exit(1)

ht = sys.argv[1]
ds_name = sys.argv[2]

assert ht in halo_types, f"{ht} is not a valid halo type: Options are {halo_types}"


print(f"Working from {os.getcwd()}")
print("Reading redshifts cache...")
with open(f".data/{ds_name}/{ht}/redshifts.pickle","rb") as f:
    d=pickle.load(f)

zs = d.keys()

print("Writing redshifts to txt file...")
with open(f".data/{ds_name}/{ht}/redshifts.txt","w") as f:
    for z in zs:
        f.write(f"{z} ")

print("DONE")
