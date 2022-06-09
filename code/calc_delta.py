import numpy as np
import yt
import sys
from . import cli

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

    snapshot_f_name = f"/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/data/snapdir_{snapshot:0>3}/snapshot_{snapshot:0>3}.0.hdf5"

    # load in the simulation
    data_set = yt.load(snapshot_f_name, unit_base=units)

    z = data_set.current_redshift

    a = 1 / (1+z)

    # define a region containing the full box and get its density
    region = data_set.r[:, :, :]

    rho_bar = region.quantities.total_mass()[1] / (data_set.domain_width[0]*a)**3

    # overdensities
    delta = []

    # give units to the sphere radius
    radius_units = radius * data_set.units.Mpc / data_set.units.h

    R = radius_units.to('code_length')

    # create spheres at random locations from the file and get their overdensities
    for centres in random_centres:

        sp = data_set.sphere(centres, R)

        rho = sp.quantities.total_mass()[1] / (4*np.pi/3 * (a*R)**3)

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
