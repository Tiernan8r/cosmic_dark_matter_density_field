import numpy as np
import yt
import yt.extensions.legacy

import helpers

yt.enable_parallelism()

num_snapshots = 299
snapshots = np.arange(0, num_snapshots)

storage = {}

for sto, snapshot in yt.parallel_objects(snapshots, num_snapshots, storage=storage):

    f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/data/groups_{snapshot:0>3}/fof_subhalo_tab_{snapshot:0>3}.0.hdf5"

    # load in the simulation
    ds = yt.load(f_name)
    ad = ds.all_data()

    for group_num in ad["Group", "particle_identifier"]:
        group = ds.halo("Group", group_num)

        mass = group.mass
        
