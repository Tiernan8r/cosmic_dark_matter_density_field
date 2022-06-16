import numpy as np
import yt
import yt.extensions.legacy

snapshot = 15

f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/rockstar/halos_{snapshot:0>3}.0.bin"

# load in the simulation
ds = yt.load(f_name)
