import matplotlib.pyplot as plt
import numpy as np
import yt

# MPI stuff

yt.enable_parallelism()

ss = np.arange(0, 102)

storage = {}


# Sphere centers from a file

c = np.loadtxt("random_locs.txt", max_rows=500)


# Sphere radius

r = 50


# 102 snapshots on different cores

for sto, s in yt.parallel_objects(ss, 102, storage=storage):

    units = {"length": (1.0, "Mpc/h")}

    f_name = f"/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/data/snapdir_{s:0>3}/snapshot_{s:0>3}.0.hdf5"  # noqa: E501

    # load in the simulation
    ds = yt.load(f_name, unit_base=units)

    z = ds.current_redshift

    a = 1 / (1+z)

    # define a region containing the full box and get its density

    cg = ds.r[:, :, :]

    rho_bar = cg.quantities.total_mass()[1] / (ds.domain_width[0]*a)**3

    # overdensities

    delta = []

    # give units to the sphere radius

    l_units = ds.length_unit
    r_un = r * l_unit

    R = r_un.to("code_length")

    # create spheres at random locations from the file and get their
    # overdensities

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

    with open("z_full.txt", 'w') as fo:

        for x in z_arr:

            fo.write(str(z) + '\n')

    with open("delta_final_50Mpc.txt", 'w') as fo:

        for x in delta_arr:

            for y in x:

                fo.write(str(y) + " ")

            fo.write("\n")

    a_arr = 1 / (1+z_arr)

    # plot the data

    for i in range(len(c)):

        plt.plot(a_arr, delta_arr.T[i], alpha=0.1)

    plt.title("Overdensity evolution with cosmic scale factor")

    plt.xlabel("Scale factor $a$")

    plt.ylabel("Overdensity $\delta$")  # noqa: W605

    plt.savefig("delta_vs_a_final_50Mpc.png")
