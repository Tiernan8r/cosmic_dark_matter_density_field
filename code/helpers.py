import os
import re
from typing import List, Tuple

ROOT = "/disk12/legacy/"

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

PATHS = [ROOT + ds for ds in DATA_SETS]
TEST_PATHS = [ROOT + tds for tds in TEST_DATA_SETS]
ALL_PATHS = [ROOT + ads for ads in ALL_DATA_SETS]

ROCKSTAR = "dm_gadget/rockstar/"
DATA = "dm_gadget/data/"

GROUP_PATTERN = DATA + "groups_{0:0>3}/fof_subhalo_tab_{0:0>3}.0.hdf5"
SNAPSHOT_PATTERN = DATA + "snapdir_{0:0>3}/snapshot_{0:0>3}.0.hdf5"
ROCKSTAR_PATTERN = ROCKSTAR + "halos_{0:0>3}.0.bin"

groups_regex = re.compile(".*fof_subhalo_tab_\d{3}.0.hdf5$")
rockstar_regex = re.compile(".*halos_\d{3}.0.bin$")


def find_halos(data_dir: str) -> Tuple[List[str], List[str]]:
    groups = []
    rockstars = []

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if groups_regex.match(file):
                groups.append(root + "/" + file)
            elif rockstar_regex.match(file):
                rockstars.append(root + "/" + file)

    return groups, rockstars


def gen_paths(data_sets: List[str], pattern: str) -> List[str]:
    paths = []
    for ds in data_sets:
        paths.append(ROOT + ds + pattern)
    return paths


groups = gen_paths(DATA_SETS, GROUP_PATTERN)
snapshots = gen_paths(DATA_SETS, SNAPSHOT_PATTERN)
rockstars = gen_paths(DATA_SETS, ROCKSTAR_PATTERN)

test_groups = gen_paths(TEST_DATA_SETS, GROUP_PATTERN)
test_snapshots = gen_paths(TEST_DATA_SETS, SNAPSHOT_PATTERN)
test_rockstars = gen_paths(TEST_DATA_SETS, ROCKSTAR_PATTERN)
