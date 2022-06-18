import numpy as np
import yt
import sys
import code.util.cli as cli

mappings = {
    "-h": "--help",
    "-n": "--num-snapshots",
    "-r": "--radius"
}

# Read any cli input
flags, vals = cli.parse_input(sys.argv[1:], mapping=mappings)

# MPI stuff
n_snapshots = int(flags.get("--num-snapshots", 102))

# Sphere radius
radius = int(flags.get("--radius", 50))

yt.enable_parallelism()

snapshots = np.arange(0, n_snapshots)

storage = {}

# Sphere centers from a file
random_centres = np.loadtxt("examples/random_locs.txt", max_rows=500)

# 102 snapshots on different cores
for sto, snapshot in yt.parallel_objects(snapshots, n_snapshots, storage=storage):

    units = {"length": (1.0, "Mpc/h")}

    f_name = f"/disk12/legacy/GVD_C700_l100n256_SLEGAC/dm_gadget/data/snapdir_{snapshot:0>3}/snapshot_{snapshot:0>3}.0.hdf5"

    # load in the simulation
    ds = yt.load(f_name, unit_base=units)

    z = ds.current_redshift

    a = 1 / (1+z)

    # define a region containing the full box and get its density
    rg = ds.r[:, :, :]

    rho_bar = rg.quantities.total_mass(
    )[1] / (ds.domain_width[0]*a)**3

    # overdensities
    delta = []

    # give units to the sphere radius
    radius_units = radius * ds.units.Mpc / ds.units.h

    R = radius_units.to('code_length')

    # create spheres at random locations from the file and get their overdensities
    for centres in random_centres:

        sp = ds.sphere(centres, R)

        V = 4/3 * np.pi * (a*R)**3

        rho = sp.quantities.total_mass()[1] / V

        delta.append((rho - rho_bar) / rho_bar)

    # store results from each process
    sto.result = delta

    sto.result_id = z


# only do once on root node
if yt.is_root():

    deltas = []
    z = []

    # get the data from storage
    for zs, dels in sorted(storage.items()):
        z.append(zs)
        deltas.append(dels)

    z_arr = np.array(z)
    delta_arr = np.array(deltas)

    # write the data
    with open("/home/tstapleton/dissertation/data/z.npy", "xb") as f:
        np.save(f, z_arr)

    with open("/home/tstapleotn/dissertationt/data/delta.npy", "xb") as f:
        np.save(delta_arr)
