import yt
import yt.extensions.legacy

f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/rockstar/hlists/hlist_1.00000.list"

ds=yt.load(f_name)
ds.field_list