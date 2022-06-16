import numpy as np
import yt
import yt.extensions.legacy
from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

snapshot = 0


units = {"length": (1.0, "Mpc/h")}

snap_f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/data/snapdir_{snapshot:0>3}/snapshot_{snapshot:0>3}.0.hdf5"
hc_f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/data/groups_{snapshot:0>3}/fof_subhalo_tab_{snapshot:0>3}.0.hdf5"

# load in the simulation
data_set = yt.load(snap_f_name, unit_base=units)

halo_data_set = yt.load(hc_f_name)
halo_data_set.parameters["format_revision"] = 2

halo_catalog = HaloCatalog(data_ds=data_set, halos_ds=halo_data_set)