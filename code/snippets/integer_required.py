import yt
import yt.extensions.legacy

# halo file 101 corresponds to z=0
REDSHIFT_NUMBER = 22
DATAFILE = "/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/rockstar/halos_{0:0>3}.0.bin"  # noqa: E501

fname = DATAFILE.format(REDSHIFT_NUMBER)

ds = yt.load(fname)
ad = ds.all_data()
