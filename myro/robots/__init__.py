import importlib
import math
import os
import string
import sys
import time
import types

from myro.robots.device import *

__author__ = "Joshua Arulsamy"


def file_exists(file_name):
    from posixpath import exists

    if type(file_name) == type(""):
        if len(file_name) == 0:
            return 0
        else:
            return exists(file_name)
    else:
        raise AttributeError("filename nust be a string")


def loadINIT(filename, engine=0, redo=0, brain=0, args=None):
    path = filename.split("/")
    modulefile = path.pop()  # module name
    module = modulefile.split(".")[0]
    search = string.join(path, "/")
    oldpath = sys.path[:]  # copy
    sys.path.insert(0, search)
    print(("Attempting to import '%s'..." % module))
    exec("import " + module + " as userspace")
    importlib.reload(userspace)
    print(("Loaded '%s'!" % userspace.__file__))
    sys.path = oldpath
    try:
        userspace.INIT
    except AttributeError:
        raise ImportError("your program needs an INIT() function")
    if brain is 0:
        if engine is 0:
            retval = userspace.INIT()
            return retval
        else:
            if args:
                retval = userspace.INIT(engine, args)
                return retval
            else:
                retval = userspace.INIT(engine)
                return retval
    else:
        retval = userspace.INIT(engine, brain)
        return retval


def commas(lyst):
    """
    Used to turn an enumeration into a comma-separated string of 'items'.
    Example:
    >>> commas([1, 2, 3, 4])
    '1', '2', '3', '4'
    """
    retval = ""
    for i in lyst:
        if retval:
            retval += ", '%s'" % i
        else:
            retval = "'%s'" % i
    return retval

