import re

# Log file parameters
LOG_FILENAME = "logging.yml"

# Configuration parameters:
CONFIGURATION_FILE = "configs/default.yml"

# Subpath for rockstar files
ROCKSTAR = "dm_gadget/rockstar/"
# Subpath for snapshot/group files
DATA = "dm_gadget/data/"

# Regexes to match against the appropriate file naming convention

groups_regex = re.compile("^.*fof_(subhalo_)?tab_(\d{3}).0.hdf5$")  # noqa: W605
rockstar_regex = re.compile("^.*(halos_(\d{3}).0.bin)$")  # noqa: W605
snapshots_regex = re.compile("^.*(snapshot_(\d{3}).0.hdf5)$")  # noqa: W605

# Regex to match against the root dir rockstar files are stored in
rockstar_root_regex = re.compile(".*rockstar/$")

# Regex to match against the naming pattern of the simulation data sets
sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC).*$")  # noqa: W605, E501

# Keys used in the helpers cache:
REDSHIFTS_KEY = "redshifts"
DIR_KEY = "dirs"
SNAPSHOTS_KEY = "snapshots"
GROUPS_KEY = "groups"
ROCKSTARS_KEY = "rockstars"

COORDINATES_CACHE_NAME = "coordinates"

# Keys used in the cache
TOTAL_MASS_FUNCTION_KEY = "all_masses"
MASS_FUNCTION_KEY = "masses"
RHO_BAR_KEY = "rho_bar"
RHO_BAR_0_KEY = "rho_bar_0"
OVERDENSITIES_KEY = "overdensities"
REDSHIFT_KEY = "redshift"
STD_DEV_KEY = "standard_deviation"
PRESS_SCHECHTER_KEY = "press_schechter"
UNITS_KEY = "units"
UNITS_PS_MASS = "ps_mass"
UNITS_PS_STD_DEV = "ps_std_dev"
SPHERES_KEY = "spheres"
