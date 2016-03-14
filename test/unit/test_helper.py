from functools import wraps

import kiwi.logger
import logging

kiwi.logger.init()

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
