import re

# Log file parameters

LOG_FILENAME = "logging.json"

# Data set parameters

ROOT = "/disk12/legacy/"
SIM_NAME = "GVD_C700_l1600n2048_SLEGAC"
SIM_FOLDER = f"{SIM_NAME}/"

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

# Constants for helpers.py:

# All data set names
DATA_SETS = [
    "GVD_C700_l100n1024_SLEGAC/",
    "GVD_C700_l100n2048_SLEGAC/",
    "GVD_C700_l10n1024_SLEGAC/",
    "GVD_C700_l1600n2048_SLEGAC/",
    "GVD_C900_l100n2048_SLEGAC/",
    "GVD_C900_l1600n2048_SLEGAC/",
]
TEST_DATA_SETS = [
    "GVD_C700_l100n256_SLEGAC/",
    "GVD_C700_l1600n256_SLEGAC/",
    "GVD_C700_l1600n64_SLEGAC/",
]
ALL_DATA_SETS = sorted(DATA_SETS + TEST_DATA_SETS)

# List of paths to all the data sets

PATHS = [ROOT + ds for ds in DATA_SETS]
TEST_PATHS = [ROOT + tds for tds in TEST_DATA_SETS]
ALL_PATHS = [ROOT + ads for ads in ALL_DATA_SETS]

# Subpath for rockstar files
ROCKSTAR = "dm_gadget/rockstar/"
# Subpath for snapshot/group files
DATA = "dm_gadget/data/"

# Naming pattern for group files
GROUP_PATTERN = DATA + "groups_{0:0>3}/fof_subhalo_tab_{0:0>3}.0.hdf5"
# Naming pattern for snapshot files
SNAPSHOT_PATTERN = DATA + "snapdir_{0:0>3}/snapshot_{0:0>3}.0.hdf5"
# Naming pattern for rockstar files
ROCKSTAR_PATTERN = ROCKSTAR + "halos_{0:0>3}.0.bin"

# Regexes to match against the appropriate file naming convention

groups_regex = re.compile("^fof_(subhalo_)?tab_\d{3}.0.hdf5$")
rockstar_regex = re.compile("^halos_\d{3}.0.bin$")
snapshots_regex = re.compile("^snapshot_\d{3}.0.hdf5$")

# Regex to match against the root dir rockstar files are stored in
rockstar_root_regex = re.compile(".*rockstar/$")

# Regex to match against the naming pattern of the simulation data sets
sim_regex = re.compile("^(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC)$")

# Regex to find redshifts from rockstar files
rockstar_ascii_reg = re.compile("^(halos_(\d+).0).ascii$")
rockstar_a_factor = re.compile("^#a = (.*)$")

# Path to the cache used to optimise helpers functions
PATH_TO_HELPERS_CACHE = "../data/helpers.pickle"

# Keys used in the helpers cache:
REDSHIFTS_KEY = "redshifts"
DIR_KEY = "dirs"
SNAPSHOTS_KEY = "snapshots"
GROUPS_KEY = "groups"
ROCKSTARS_KEY = "rockstars"

# Path to the cache used to store random coords generated
PATH_TO_COORDS_CACHE = "../data/coordinates.pickle"

# Path to cache for calculated values
PATH_TO_CALCULATIONS_CACHE = "../data/calculations.pickle"
# Keys used in the cache
TOTAL_MASS_FUNCTION_KEY = "all_masses"
MASS_FUNCTION_KEY = "masses"
RHO_BAR_KEY = "rho_bar"
OVERDENSITIES_KEY = "overdensities"
REDSHIFT_KEY = "redshift"