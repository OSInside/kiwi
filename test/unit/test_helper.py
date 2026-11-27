import sys
import copy
from typing import Any, Dict, Optional, Tuple

from kiwi.xml_description import XMLDescription

# default commandline used for any test, overwrite when needed
sys.argv = [
    sys.argv[0],
    'system',
    'prepare',
    '--description',
    'description',
    '--root',
    'directory',
]
argv_kiwi_tests = sys.argv


# parse results of the image descriptions loaded by load_description
_loaded_descriptions: Dict[Tuple[str, Optional[str]], Any] = {}


def load_description(
    description: str, derived_from: Optional[str] = None
) -> Any:
    """
    Parse result of the given image description, see XMLDescription.load

    Loading a description runs the markup conversion, the XSLT
    processing and the schema validation, which takes most of the
    time of many tests. Thus every description is loaded once per
    test process. Each call returns a copy of the parse result,
    such that tests can change it without affecting other tests

    :param str description: path to the image description
    :param str derived_from: path to base description file
    """
    key = (description, derived_from)
    if key not in _loaded_descriptions:
        _loaded_descriptions[key] = XMLDescription(
            description, derived_from
        ).load()
    return copy.deepcopy(_loaded_descriptions[key])
