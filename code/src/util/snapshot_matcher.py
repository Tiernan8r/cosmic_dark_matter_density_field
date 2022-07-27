import logging

import src.util.halo_finder as halo_finder
from src import data, enum
from src.const.constants import sim_regex


def match_snapshot(conf, ds_cache, hf: str) -> str:
    logger = logging.getLogger(
        __name__ + "." + match_snapshot.__name__)

    sim_name = sim_regex.match(hf).group(1)

    snaps_finder = halo_finder.HalosFinder(
        enum.DataType.SNAPSHOT, conf.sim_data.root, sim_name)

    ds = ds_cache.load(hf)
    z = ds.current_redshift
    logger.debug(f"Finding snapshot file that matches a redshift of: {z}")

    snaps_files = snaps_finder.filter_data_files([z])

    sfname = snaps_files[0]

    logger.debug(
        f"Found snapshot file '{sfname}' that is closest match to this redshift")

    return sfname
