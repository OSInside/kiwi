import inspect
import pkgutil
import pytest
import re

import kiwi


def members(module, predicate=None):
    """Yields all functions of a module if predicate=None

    :param module: the given module to search for members
    :type module: :class:`module`
    :param predicate: a function with expects an object and returns True or False
                      see :func:`inspect.isfunction` as an example
    :type prediate: :class:`function`
    """
    predicate = inspect.isfunction if predicate is None else predicate
    for _, func, in inspect.getmembers(module, predicate):
        if func.__module__ == module.__name__:
            yield func


def getmodules(module, predicate=None):
    """Yields recursively sub module names from a given module

    :param module: the given module to search for members
    :type module: :class:`module`
    :param predicate: a function with expects an object and returns True or False
                      see :func:`inspect.isfunction` as an example
    :type prediate: :class:`function`
    """
    prefix = module.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(module.__path__, prefix):
        module = importer.find_module(modname).load_module(modname)
        yield from members(module, predicate)
        if ispkg:
            getmodules(module, predicate)
        del module


def getallfunctions(module):
    yield from getmodules(module)

# List of qualified function names as regex to ignore
IGNORELIST=(r"kiwi\.xml_parse\.(.*)",
            )
IGNORELIST = tuple(re.compile(p) for p in IGNORELIST)

def ignore(func):
    """Check if function should be ignored

    :param func: function
    :return: True (=ignore) or False (=don't ignore)
    """
    fname = func.__name__
    if fname.startswith("_"):
        # Ignore any private functions
        return False
    # Use now the complete qualified function name:
    fname = "%s.%s" % (func.__module__, func.__name__)
    print(">>>", fname)
    return not any(pattern.search(fname) for pattern in IGNORELIST)

# Only add modules/functions starting not with "_"; this would indicate a private
# member.
modfuncs = [ff for ff in getallfunctions(kiwi) if ignore(ff)]
# modfuncs = [ff for ff in modfuncs if ff.__name__ not in IGNORELIST]
modfuncsnames = ["%s.%s" % (ff.__module__, ff.__name__) for ff in modfuncs]


@pytest.mark.parametrize("func",
                         modfuncs,
                         ids=modfuncsnames
                         )
def test_docstrings_nonempty(func):
    """Test if docstring is not empty"""
    fname = func.__name__
    doc = func.__doc__

    assert doc is not None, "Need an non-empty docstring for %r" % fname


@pytest.mark.parametrize("func",
                         modfuncs,
                         ids=modfuncsnames
                         )
def test_docstrings_args(func):
    """Test if docstring contains description of all parameters"""
    fname = ".".join([func.__module__, func.__name__])
    doc = func.__doc__

    assert doc is not None
    if func.__code__.co_argcount:
        for arg in inspect.getargspec(func).args:
            m = re.search(":param\s+\w*\s*%s:" % arg, doc)
            assert m, "Func argument %r " \
                "not explained in docstring " \
                "of function %r" % (arg, fname)
