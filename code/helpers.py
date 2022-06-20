import os
import re
from typing import List, Tuple

ROOT = "/disk12/legacy/"

DATA_SETS = [
    # "GVD_C700_l100n1024_SLEGAC/",
    # "GVD_C700_l100n2048_SLEGAC/",
    # "GVD_C700_l10n1024_SLEGAC/",
    "GVD_C700_l1600n2048_SLEGAC/",
    # "GVD_C900_l100n2048_SLEGAC/",
    # "GVD_C900_l1600n2048_SLEGAC/",
]

TEST_DATA_SETS = [
    "GVD_C700_l100n256_SLEGAC/",
    # "GVD_C700_l1600n256_SLEGAC/",
    # "GVD_C700_l1600n64_SLEGAC/",
]

ALL_DATA_SETS = sorted(DATA_SETS + TEST_DATA_SETS)

PATHS = [ROOT + ds for ds in DATA_SETS]
TEST_PATHS = [ROOT + tds for tds in TEST_DATA_SETS]
ALL_PATHS = [ROOT + ads for ads in ALL_DATA_SETS]

ROCKSTAR = "dm_gadget/rockstar/"
DATA = "dm_gadget/data/"

GROUP_PATTERN = DATA + "groups_{0:0>3}/fof_subhalo_tab_{0:0>3}.0.hdf5"
SNAPSHOT_PATTERN = DATA + "snapdir_{0:0>3}/snapshot_{0:0>3}.0.hdf5"
ROCKSTAR_PATTERN = ROCKSTAR + "halos_{0:0>3}.0.bin"

groups_regex = re.compile(".*fof_(subhalo_)?tab_\d{3}.0.hdf5$")
rockstar_regex = re.compile(".*halos_\d{3}.0.bin$")
snapshots_regex = re.compile(".*snapshot_\d{3}.0.hdf5$")

rockstar_root_regex = re.compile(".*rockstar$")

sim_regex = re.compile("^.*(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC).*$")


def find_halos(data_dir: str) -> Tuple[List[str], List[str], List[str]]:
    groups = []
    rockstars = []
    snapshots = []

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if groups_regex.match(file):
                groups.append(root + "/" + file)
            elif rockstar_regex.match(file) and rockstar_root_regex.match(root):
                rockstars.append(root + "/" + file)
            elif snapshots_regex.match(file):
                snapshots.append(root + "/" + file)

    return sorted(groups), sorted(rockstars), sorted(snapshots)
