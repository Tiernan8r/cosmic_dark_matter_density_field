import re

# Log file parameters

LOG_FILENAME = "logging.yaml"

# Data set parameters

ROOT = "/disk12/legacy/"
SIM_NAME = "GVD_C700_l1600n2048_SLEGAC"
SIM_FOLDER = f"{SIM_NAME}/"

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC).*$")

# Sampling parameters

NUM_SPHERE_SAMPLES = 1000
NUM_HIST_BINS = 1000
NUM_OVERDENSITY_HIST_BINS = 1000

DESIRED_REDSHIFTS = [0, 1, 2, 6, 10]
DESIRED_RADII = [50]
# DESIRED_RADII = [10, 20, 50, 100]

# Plot save path parameters

MASS_FN_PLOTS_DIR = "../plots/mass_function/{0}/"
MASS_FN_PLOTS_FNAME_PTRN = MASS_FN_PLOTS_DIR + \
    "mass_function_r{1:.2f}-z{2:.2f}.png"

OVERDENSITY_PLOTS_DIR = "../plots/deltas/{0}/"
OVERDENSITY_PLOTS_FNAME_PTRN = OVERDENSITY_PLOTS_DIR + \
    "overdensity_r{1:.2f}-z{2:.2f}.png"
