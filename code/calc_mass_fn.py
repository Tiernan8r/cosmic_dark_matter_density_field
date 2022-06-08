import numpy as np
import yt

# MPI stuff
n_snapshots = 25

yt.enable_parallelism()

ss = np.arange(0, n_snapshots)

storage = {}


# Sphere centers from a file
c = np.loadtxt("examples/random_locs.txt", max_rows=10)


# Sphere radius
r = 2


# 102 snapshots on different cores
for sto, s in yt.parallel_objects(ss, n_snapshots, storage=storage):

    units = {"length": (1.0, "Mpc/h")}

    f_name = f"/disk12/legacy/GVD_C700_l10n1024_SLEGAC/dm_gadget/data/snapdir_{s:0>3}/snapshot_{s:0>3}.0.hdf5"

    # load in the simulation
    ds = yt.load(f_name, unit_base=units)

    z = ds.current_redshift

    a = 1 / (1+z)

    # define a region containing the full box and get its density
    cg = ds.r[:]

    rho_bar = cg.quantities.total_mass()[1] / (ds.domain_width[0]*a)**3

    # overdensities
    delta = []

    # give units to the sphere radius
    r_un = r * ds.units.Mpc / ds.units.h

    R = r_un.to('code_length')

    # create spheres at random locations from the file and get their overdensities
    for cc in c:

        sp = ds.sphere(cc, R)

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
    with open("/home/tstapleton/dissertation/data/mass_fn_z.npy", "xb") as f:
        np.save(f, z_arr)

    with open("/home/tstapleton/dissertation/data/mass_fn_delta.npy", "xb") as f:
        np.save(delta_arr)
