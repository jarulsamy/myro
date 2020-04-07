__author__ = "Joshua Arulsamy"


def file_exists(file_name):
    from posixpath import exists

    if isinstance(file_name, str):
        if len(file_name) == 0:
            return 0
        else:
            return exists(file_name)
    else:
        raise AttributeError("filename nust be a string")


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
