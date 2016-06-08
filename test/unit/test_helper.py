from functools import wraps

import kiwi.logger
import sys
import logging
from io import BytesIO
from mock import MagicMock, patch

kiwi.logger.log.setLevel(logging.WARN)


class raises(object):
    """
    exception decorator as used in nose, tools/nontrivial.py
    """
    def __init__(self, *exceptions):
        self.exceptions = exceptions
        self.valid = ' or '.join([e.__name__ for e in exceptions])

    def __call__(self, func):
        name = func.__name__

        def newfunc(*args, **kw):
            try:
                func(*args, **kw)
            except self.exceptions:
                pass
            except:
                raise
            else:
                message = "%s() did not raise %s" % (name, self.valid)
                raise AssertionError(message)
        newfunc = wraps(func)(newfunc)
        return newfunc


patch_open = patch("{0}.open".format(sys.version_info.major < 3 and
                                     "__builtin__" or "builtins"))

def mock_open(data=None):
    '''
    Mock "open" function.

    :param data:
    :return:
    '''
    data = BytesIO(data)
    mock = MagicMock(spec=file)
    handle = MagicMock(spec=file)
    handle.write.return_value = None
    handle.__enter__.return_value = data or handle
    mock.return_value = handle

    return mock
