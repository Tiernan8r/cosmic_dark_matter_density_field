import yt
import yt.extensions.legacy

redshifts = range(101, -1, -1)

fname = "/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/rockstar/halos_{0:0>3}.0.bin"

map = {}

for rs in redshifts:
    rck = fname.format(rs)
    print(f"Opening '{rck}'")

    ds = yt.load(rck)

    z = ds.current_redshift

    v = (ds.domain_width).to(ds.length_unit)

    map[z] = v

with open("redshift_mappings.txt","w") as f:
    for k in map.keys():
        f.write(f"{k} = {map[k]}\n")

