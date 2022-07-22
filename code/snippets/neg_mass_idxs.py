import numpy as np
import yt

def neg_mass_idxs(ds):
    ad = ds.all_data()

    all_masses = ad["halos", "particle_mass"]

    neg_idxs = np.where(all_masses < 0)

    neg_masses = all_masses[neg_idxs]

    neg_sum = np.sum(neg_masses)

    print(f"Total Negative mass: {neg_sum}")
    print(f"Negative mass array: {neg_masses}")

# halo file 101 corresponds to z=0
REDSHIFT_NUMBER = 101
DATAFILE = "/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/rockstar/halos_{0:0>3}.0.bin"

fname = DATAFILE.format(REDSHIFT_NUMBER)

ds = yt.load(fname)
print("With 'format_revision' = 1")
neg_mass_idxs(ds)

ds = yt.load(fname)
ds.parameters["format_revision"] = 2
print("With 'format_revision' = 2")
neg_mass_idxs(ds)

import yt.extensions.legacy
ds = yt.load(fname)
print("With yt.extentions.legacy, 'format_revision' = 1")
neg_mass_idxs(ds)

ds = yt.load(fname)
ds.parameters["format_revision"] = 2
print("With yt.extensions.legacy, 'format_revision' = 2")
neg_mass_idxs(ds)

