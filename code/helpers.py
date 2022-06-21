import math
import os
import re
from typing import Dict, List, Tuple

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

groups_regex = re.compile("^fof_(subhalo_)?tab_\d{3}.0.hdf5$")
rockstar_regex = re.compile("^halos_\d{3}.0.bin$")
snapshots_regex = re.compile("^snapshot_\d{3}.0.hdf5$")

rockstar_root_regex = re.compile(".*rockstar/$")

sim_regex = re.compile("^(GVD_C(\d{3})_l(\d+)n(\d+)_SLEGAC)$")


def _find_directories(sim_name: str) -> Tuple[str, str, str]:
    if not sim_regex.match(sim_name):
        return "/tmp", "/tmp", "/tmp"

    snapshots_root = ROOT + sim_name + "/" + DATA
    groups_root = snapshots_root
    rockstar_root = ROOT + sim_name + "/" + ROCKSTAR

    return snapshots_root, groups_root, rockstar_root


def find_data_files(sim_name: str) -> Tuple[List[str], List[str], List[str]]:

    snap, group, rock = _find_directories(sim_name)

    def find(dirname: str, file_reg: re.Pattern, root_reg: re.Pattern = None):
        l = []

        for root, dirs, files in os.walk(dirname):
            for file in files:
                if file_reg.match(file):
                    if root_reg is not None:
                        if not root_reg.match(root):
                            continue
                    l.append(root + file)

        return l

    groups = find(group, groups_regex)
    rockstars = find(rock, rockstar_regex, rockstar_root_regex)
    snapshots = find(snap, snapshots_regex)

    return sorted(snapshots), sorted(groups), sorted(rockstars),


rockstar_ascii_reg = re.compile("^(halos_(\d+).0).ascii$")
rockstar_a_factor = re.compile("^#a = (.*)$")


def determine_redshifts(sim_name: str) -> Dict[float, str]:
    _, _, rock = _find_directories(sim_name)

    map = {}

    for dirname, subdirs, files in os.walk(rock):
        for file in files:
            if rockstar_ascii_reg.match(file):
                with open(dirname + file) as f:
                    # Read the second line in the vals file, which says the expansion factor
                    a = f.readlines()[1]
                    a_val = float(rockstar_a_factor.match(a).group(1))
                    # convert from comoving to redshift
                    z = (1 / a_val) - 1
                    map[z] = rockstar_ascii_reg.match(file).group(2)

    return map


def filter_redshifts(sim_name: str, desired: List[float], tolerance=0.02) -> Dict[float, str]:
    all_redshifts = determine_redshifts(sim_name)

    redshifts = {}

    for k in all_redshifts.keys():
        for z in desired:
            if math.isclose(k, z, rel_tol=tolerance) and k not in redshifts:
                redshifts[k] = all_redshifts[k]
    return redshifts


def filter_data_files(sim_name: str, desired: List[float], tolerance=0.02) -> Tuple[List[str], List[str], List[str]]:
    redshifts = filter_redshifts(sim_name, desired, tolerance)
    snaps, groups, rocks = find_data_files(sim_name)

    file_idxs = redshifts.values()

    def filter(vals): return [
        v for v in vals if any([i in v for i in file_idxs])]

    filter_snaps = filter(snaps)
    filter_groups = filter(groups)
    filter_rocks = filter(rocks)

    return filter_snaps, filter_groups, filter_rocks
