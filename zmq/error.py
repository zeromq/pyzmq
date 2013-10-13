"""0MQ Error classes and functions."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class ZMQBaseError(Exception):
    """Base exception class for 0MQ errors in Python."""
    pass

class ZMQError(ZMQBaseError):
    """Wrap an errno style error.

    Parameters
    ----------
    errno : int
        The ZMQ errno or None.  If None, then ``zmq_errno()`` is called and
        used.
    msg : string
        Description of the error or None.
    """
    errno = None

    def __init__(self, errno=None, msg=None):
        """Wrap an errno style error.

        Parameters
        ----------
        errno : int
            The ZMQ errno or None.  If None, then ``zmq_errno()`` is called and
            used.
        msg : string
            Description of the error or None.
        """
        from zmq.backend import strerror, zmq_errno
        if errno is None:
            errno = zmq_errno()
        if isinstance(errno, int):
            self.errno = errno
            if msg is None:
                self.strerror = strerror(errno)
            else:
                self.strerror = msg
        else:
            if msg is None:
                self.strerror = str(errno)
            else:
                self.strerror = msg
        # flush signals, because there could be a SIGINT
        # waiting to pounce, resulting in uncaught exceptions.
        # Doing this here means getting SIGINT during a blocking
        # libzmq call will raise a *catchable* KeyboardInterrupt
        # PyErr_CheckSignals()

    def __str__(self):
        return self.strerror
    
    def __repr__(self):
        return "ZMQError('%s')"%self.strerror


class ZMQBindError(ZMQBaseError):
    """An error for ``Socket.bind_to_random_port()``.
    
    See Also
    --------
    .Socket.bind_to_random_port
    """
    pass


class NotDone(ZMQBaseError):
    """Raised when timeout is reached while waiting for 0MQ to finish with a Message
    
    See Also
    --------
    .MessageTracker.wait : object for tracking when ZeroMQ is done
    """
    pass


class ContextTerminated(ZMQError):
    """Wrapper for zmq.ETERM
    
    .. versionadded:: 13.0
    """
    pass


class Again(ZMQError):
    """Wrapper for zmq.EAGAIN
    
    .. versionadded:: 13.0
    """
    pass


def _check_rc(rc, errno=None):
    """internal utility for checking zmq return condition
    
    and raising the appropriate Exception class
    """
    from zmq.backend import zmq_errno
    from errno import EINTR
    from zmq import EAGAIN, ETERM
    if rc < 0:
        if errno is None:
            errno = zmq_errno()
        if errno == EAGAIN:
            raise Again(errno)
        elif errno == ETERM:
            raise ContextTerminated(errno)
        else:
            raise ZMQError(errno)


__all__ = ['ZMQBaseError', 'ZMQBindError', 'ZMQError', 'NotDone', 'ContextTerminated', 'Again']
