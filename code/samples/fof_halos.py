import yt
import yt.extensions.legacy

snapshot = 299

f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/data/groups_{snapshot:0>3}/fof_subhalo_tab_{snapshot:0>3}.0.hdf5"  # noqa: E501

# load in the simulation
ds = yt.load(f_name)
# ds.parameters["format_revision"] = 2

group = ds.halo("Group", 0)
