import pickle

import numpy as np
import yt
import yt.extensions.legacy

map={}

for rs in range(29, 102):
    DATAFILE = "/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/rockstar/halos_{0:0>3}.0.bin"  # noqa: E501

    fname = DATAFILE.format(rs)
    print("RCK=", fname)

    ds = yt.load(fname)

    try:
        ad = ds.all_data()
        masses = ad["halos", "particle_mass"]

        print("Filtering for neg masses")
        neg_idxs = np.where(masses < 0)

        neg_x = ad["halos", "particle_position_x"]
        neg_y = ad["halos", "particle_position_y"]
        neg_z = ad["halos", "particle_position_z"]

        print("Compiling coords")
        coords = []
        for i in neg_idxs[0]:
            x, y, z = neg_x[i], neg_y[i], neg_z[i]
            coord = (x, y, z)

            coords.append(coord)

        z = ds.current_redshift
        print("Saving to map\n")

        map[z] = coords
    except Exception as e:
        print(e)

print("Writing result to pickle...")
with open("negs.yaml", "wb") as f:
    import yaml
    yaml.dump(map, f)
