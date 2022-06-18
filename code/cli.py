import re
import sys
from typing import Dict, List, Tuple

flag_short_pattern = re.compile("-.+")
flag_long_pattern = re.compile("--.+")


def parse_input(args: List[str], mapping: Dict[str, str] = {}) -> Tuple[Dict[str, str], List[str]]:
    """
    Convert the given list of cli arguments into a mapping between the
    CLI flags and their value, and a list or CLI arguments
    :param List[str] args: The CLI arguments
    :param Dict[str, str] mapping: Optional mapping of abbreviated cli
        inputs to longer ones
    returns:
        Tuple[Dict[str, str], List[str]]: A tuple of the flags dictionary
            and the arguments list.
    """
    d = {}  # Map the flags to the values in a dictionary
    v = []  # Store all unmapped values in a list

    n = len(args)
    i = 0
    while i < n:
        arg = args[i]

        if (flag_short_pattern.match(arg) or flag_long_pattern.match(arg)):
            val = ""
            if i + 1 < n:
                val = args[i+1]

            # Convert the short flag names to the long ones
            if arg in mapping:
                arg = mapping[arg]

            if arg in d:
                print(
                    f"Duplicate flag '{arg}' detected, skipping...",
                    file=sys.stderr)
                i += 2
                continue
            d[arg] = val
            i += 2
        else:
            v.append(arg)
            i += 1

    return d, v
