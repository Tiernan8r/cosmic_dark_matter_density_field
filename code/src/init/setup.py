import logging
import logging.config
import os
from typing import Tuple

import yaml
import yt
from src.cache import dataset
from src.const.constants import LOG_FILENAME
from src.init import conf as config


def setup(args) -> Tuple[config.Configuration, dataset.CachedDataSet]:
    """
    Default initialisation steps
    """

    setup_logging()
    logger = logging.getLogger(__name__ + "." + setup.__name__)

    logger.debug("Logging initialised")

    # Read the configuration file from the args if provided.
    conf = config.new(args)

    logger.debug(f"Configuration read from file '{conf._config_file}'")

    yt.enable_parallelism()
    logger.info("Parallelism enabled...")

    logger.debug(f"Reading data set(s) in: {conf.paths}")

    ds_cache = dataset.new()
    logger.debug("Created data set cached reader")

    return conf, ds_cache 


def setup_logging() -> logging.Logger:
    logging_path = os.path.abspath(LOG_FILENAME)
    with open(logging_path) as f:
        dict_config = yaml.safe_load(f)

    logging.config.dictConfig(dict_config)
