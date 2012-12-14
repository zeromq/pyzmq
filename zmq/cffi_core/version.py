from zmq import zmq_version_info

__version__ = '2.2dev'
__revision__ = ''

def pyzmq_version():
    """pyzmq_version()

    Return the version of pyzmq as a string.
    """
    if __revision__:
        return '@'.join([__version__,__revision__[:6]])
    else:
        return __version__

def pyzmq_version_info():
    """pyzmq_version_info()

    Return the pyzmq version as a tuple of numbers

    If pyzmq is a dev version, the patch-version will be `inf`.

    This helps comparison of version tuples in Python 3, where str-int
    comparison is no longer legal for some reason.
    """
    import re
    parts = re.findall('[0-9]+', __version__)
    parts = [ int(p) for p in parts ]
    if 'dev' in __version__:
        parts.append(float('inf'))
    return tuple(parts)


def zmq_version():
    """zmq_version()

    Return the version of ZeroMQ itself as a string.
    """
    return "%i.%i.%i" % zmq_version_info()
