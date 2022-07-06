import matplotlib.pyplot as plt
import numpy as np
import yt
import yt.extensions.legacy

# halo file 101 corresponds to z=0
REDSHIFT_NUMBER = 101
DATAFILE = "/disk12/legacy/GVD_C700_l1600n2048_SLEGAC/dm_gadget/rockstar/halos_{0:>3}.0.bin"

# Number of histogram bins to use
NUM_BINS = 100

fname = DATAFILE.format(REDSHIFT_NUMBER)

ds = yt.load(fname)
ad = ds.all_data()

masses = ad["halos", "particle_mass"].to(ds.units.Msun / ds.units.h)

print("Mass units:", masses.units)

# Volume of the box
sim_size = ds.domain_width[0].to(ds.units.Mpc / ds.units.h)
volume = sim_size ** 3

print("Volume of simulation:", volume)

# Calculate the histogram of the masses
hist, bins = np.histogram(masses, bins=NUM_BINS)

# Filter hist/bins for non-zero masses
valid_idxs = np.where(hist > 0)
hist = hist[valid_idxs]
bins = bins[valid_idxs]

# convert histogram values to number density
hist = hist / volume

z = ds.current_redshift

x = np.log(bins)
y = np.log(hist)

fig = plt.figure()
ax = fig.gca()

ax.plot(x, y)
ax.set_xscale("log")

title = f"Total Mass Function for z={z:.2f}"
fig.suptitle(title)

ax.set_xlabel("$\log{M_{vir}}$")
ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

plot_fname = f"total_mass_function_z{z}.png"
fig.savefig(plot_fname)
