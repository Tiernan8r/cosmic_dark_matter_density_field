import matplotlib.pyplot as plt
import numpy as np
import yt
import yt.extensions.legacy

# halo file 101 corresponds to z=0
REDSHIFT_NUMBER = 101
DATAFILE = "/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/rockstar/halos_{0:0>3}.0.bin"  # noqa: E501

# Number of histogram bins to use
NUM_BINS = 100

fname = DATAFILE.format(REDSHIFT_NUMBER)

ds = yt.load(fname)

# =======
# RHO BAR
# =======

ad = ds.all_data()

sim_size = ds.domain_width[0].to(ds.units.Mpc / ds.units.h)
total_volume = sim_size ** 3

total_mass = ad.quantities.total_mass()[1].to(ds.units.Msun / ds.units.h)

rho_bar = total_mass / total_volume

print("Average density over all simulation:", rho_bar)

# ===============
# Sphere Sampling
# ===============

RADIUS = 10
NUM_SPHERE_SAMPLES = 10

min = RADIUS
max = sim_size.v - RADIUS
coords = (max - min) * np.random.rand(NUM_SPHERE_SAMPLES, 3) + min

all_overdensities = []

radius_units = ds.units.Mpc
r = RADIUS * radius_units

# Volume of the sphere
volume = 4 / 3 * np.pi * r**3

for c in coords:
    sp = ds.sphere(c, RADIUS)

    mass = sp.quantities.total_mass()[1].to(ds.units.Msun / ds.units.h)
    density = mass / volume

    od = (density - rho_bar) / rho_bar
    print("Overdensity in this sphere is:", od)

    # Turn the overdensity into a one item array, so that it can
    # be concatenated to the total list
    all_overdensities = np.concatenate((all_overdensities, [od]))

# =============
# STD DEVIATION
# =============

std_dev = np.std(all_overdensities)
print("Standard Deviation is:", std_dev)

# ========
# PLOTTING
# ========

z = ds.current_redshift

print("All Overdensities:", all_overdensities)

title = f"Overdensity for z={z:.2f}"
plot_fname = f"overdensity_z{z}.png"

fig = plt.figure()
ax = fig.gca()

ax.hist(all_overdensities)

fig.suptitle(title)
ax.set_xlabel("Overdensity value")
ax.set_ylabel("Overdensity $\delta$")  # noqa: W605

fig.savefig(plot_fname)
