import numpy as np
import yt

# MPI stuff
n_snapshots = 25

yt.enable_parallelism()

snapshots = np.arange(0, n_snapshots)

storage = {}


# Sphere centers from a file
rand_centres = np.loadtxt("examples/random_locs.txt", max_rows=10)


# Sphere radius
radius = 2


# 102 snapshots on different cores
for stor, snapshot in yt.parallel_objects(snapshots, n_snapshots, storage=storage):

    units = {"length": (1.0, "Mpc/h")}

    snap_name = f"/disk12/legacy/GVD_C700_l10n1024_SLEGAC/dm_gadget/data/snapdir_{snapshot:0>3}/snapshot_{snapshot:0>3}.0.hdf5"

    # load in the simulation
    data_set = yt.load(snap_name, unit_base=units)

    z = data_set.current_redshift

    a = 1 / (1+z)

    # define a region containing the full box and get its density
    region = data_set.r[:]

    rho_bar = region.quantities.total_mass()[1] / (data_set.domain_width[0]*a)**3

    # overdensities
    delta = []

    # give units to the sphere radius
    radius_units = radius * data_set.units.Mpc / data_set.units.h

    R = radius_units.to('code_length')

    # create spheres at random locations from the file and get their overdensities
    for centre in rand_centres:

        sphere = data_set.sphere(centre, R)

        rho = sphere.quantities.total_mass()[1] / (4*np.pi/3 * (a*R)**3)

        delta.append((rho - rho_bar) / rho_bar)

    # store results from each process
    stor.result = delta

    stor.result_id = z


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
    with open("/home/tstapleton/dissertation/data/mass_fn_z.npy", "xb") as f:
        np.save(f, z_arr)

    with open("/home/tstapleton/dissertation/data/mass_fn_delta.npy", "xb") as f:
        np.save(delta_arr)
