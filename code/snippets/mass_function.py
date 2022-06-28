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

RADIUS = 10
NUM_SPHERE_SAMPLES = 10

sim_size = ds.domain_width[0]
min = RADIUS
max = sim_size.v - RADIUS
coords = (max - min) * np.random.rand(NUM_SPHERE_SAMPLES, 3) + min

mass_units = None
all_masses = []

for c in coords:
    sp = ds.sphere(c, RADIUS)

    masses = sp["halos", "particle_mass"]

    if mass_units is None:
        mass_units = masses.units

    all_masses = np.concatenate((all_masses, masses.v))

print("Mass units:", mass_units)

# Volume of the box
volume = 4 / 3 * np.pi * RADIUS**3

# Calculate the histogram of the masses
hist, bins = np.histogram(all_masses, bins=NUM_BINS)

# Filter hist/bins for non-zero masses
valid_idxs = np.where(hist > 0)
hist = hist[valid_idxs]
bins = bins[valid_idxs]

# convert histogram values to number density
hist = hist / volume

z = ds.current_redshift

title = f"Mass Function for z={z:.2f}"
plot_fname = f"mass_function_z{z}.png"

x = np.log(bins)
y = np.log(hist)

fig = plt.figure()
ax = fig.gca()

ax.plot(x, y)
ax.set_xscale("log")

fig.suptitle(title)
ax.set_xlabel("$\log{M_{vir}}$")
ax.set_ylabel("$\phi=\\frac{d \log{n}}{d \log{M_{vir}}}$")

fig.savefig(plot_fname)
