import matplotlib.pyplot as plt
import numpy as np

# Sphere centers from a file
c = np.loadtxt("examples/random_locs.txt", max_rows=500)

z_arr = np.load("/home/tstapleton/dissertation/data/z.npy")
delta_arr = np.load("/home/tstapleton/dissertation/data/delta.npy")

a_arr = 1 / (1+z_arr)

# plot the data
for i in range(len(c)):
    plt.plot(a_arr, delta_arr.T[i], alpha=0.1)

plt.title("Overdensity evolution with cosmic scale factor")
plt.xlabel("Scale factor $a$")
plt.ylabel("Overdensity $\delta$")
plt.savefig("delta_vs_a_final_50Mpc.png")
