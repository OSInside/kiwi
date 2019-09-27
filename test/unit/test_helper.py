import kiwi.logger
import sys
import logging
from io import BytesIO
from mock import MagicMock, patch

# default log level, overwrite when needed
kiwi.logger.log.setLevel(logging.WARN)

# default commandline used for any test, overwrite when needed
sys.argv = [
    sys.argv[0], 'system', 'prepare',
    '--description', 'description', '--root', 'directory'
]
argv_kiwi_tests = sys.argv

# mock open calls
patch_open = patch('builtins.open')


def mock_open(data=None):
    '''
    Mock "open" function.

    :param data:
    :return:
    '''
    data = BytesIO(data)
    mock = MagicMock()
    handle = MagicMock()
    handle.write.return_value = None
    handle.__enter__.return_value = data or handle
    mock.return_value = handle

    return mock
