import logging
import logging.config
import os

import yaml
import yt
from src.cache import caching, dataset
from src.const.constants import LOG_FILENAME
from src.data import Data
from src.init import conf as config


def setup(args) -> Data:
    """
    Default initialisation steps
    """

    setup_logging()
    logger = logging.getLogger(__name__ + "." + setup.__name__)

    logger.debug("Logging initialised")

    # Read the configuration file from the args if provided.
    conf, conf_file = config.new(args)

    logger.debug(f"Configuration read from file '{conf_file}'")

    yt.enable_parallelism()
    logger.info("Parallelism enabled...")

    ds_cache = dataset.new()
    logger.debug("Created data set cached reader")

    cache = caching.Cache()

    return Data(conf, ds_cache, cache)


def setup_logging() -> logging.Logger:
    logging_path = os.path.abspath(LOG_FILENAME)
    with open(logging_path) as f:
        dict_config = yaml.safe_load(f)

    logging.config.dictConfig(dict_config)
