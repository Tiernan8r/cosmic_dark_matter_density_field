import logging
import types
from typing import Any, Dict, List, Tuple

import yaml
from src.util.constants import CONFIGURATION_FILE
from src.util.init.yaml_loader import IncludeLoader


def new(args: List[str]) -> Tuple[types.SimpleNamespace, str]:
    logger = logging.getLogger(__name__ + "." + new.__name__)
    logger.debug(f"Initialising config parsing with arguments: {args}")

    default_config = _load(CONFIGURATION_FILE)

    config_file = CONFIGURATION_FILE
    if len(args) > 0:
        config_file = args[0]

    logger.debug(
        f"Attempting to create Configuration object with config file='{config_file}'")  # noqa: E501

    conf = _load(config_file)

    # recursively merge nested dicts
    final_config = _merge_configs(default_config, conf)

    logger.info("Read config as:")
    print(yaml.safe_dump(final_config))

    # Recursively compile into namespaces:
    namespace = _compile_namespace(final_config)

    return namespace, config_file


def _load(fname) -> Dict[str, Any]:
    with open(fname, "rb") as f:
        return yaml.load(f, Loader=IncludeLoader)


def _compile_namespace(d: Dict[str, Any]) -> types.SimpleNamespace:
    for k in d.keys():
        if type(d[k]) is dict:
            new_entry = _compile_namespace(d[k])
            d[k] = new_entry
    return types.SimpleNamespace(**d)


def _merge_configs(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
    """
    d2 overwrites d1
    """
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    overlap_keys = d1_keys & d2_keys
    d1_uniqs = d1_keys - overlap_keys
    d2_uniqs = d2_keys - overlap_keys

    final = {}
    for k in d1_uniqs:
        final[k] = d1[k]
    for k in d2_uniqs:
        final[k] = d2[k]

    for k in overlap_keys:
        val = d2[k]
        # recursively merge nested dicts
        if type(d1[k]) is dict and type(d2[k]) is dict:
            val = _merge_configs(d1[k], d2[k])
        final[k] = val

    return final
