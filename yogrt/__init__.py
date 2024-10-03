"""Determine remaining job time from a resource manager.

This provides an interface to libyogrt ("Your One Get Remaining Time
library") which supports querying various cluster resource managers to
determine the remaining time in a job.

The main method you probably care about is `yogrt.get_remaining`, which
returns the number of seconds remaining in your current job.
"""

from ._yogrt_c import lib as _yogrt_c_lib


__all__ = ['get_remaining',
           'set_remaining',
           'set_interval1',
           'set_interval2',
           'set_interval2_start',
           'get_interval1',
           'get_interval2',
           'get_interval2_start',
           'set_debug',
           'get_debug']


# These methods are all wrapped to provide typing and docstrings.

def get_remaining() -> int:
    """Return the number of seconds remaining in the current resource
    allocation.

    This may only be called from rank 0 of a parallel job.

    If the resource manager cannot be reached, or this is called
    outside of a parallel job, this will return `INT_MAX` (typically
    2^31 - 1).
    """
    return _yogrt_c_lib.yogrt_remaining()


def set_remaining(seconds: int) -> None:
    """Modify the cached remaining time.

    Args:
        seconds (int): The number of seconds to set the cached
        remaining time to.
    """
    _yogrt_c_lib.yogrt_set_remaining(seconds)


def set_interval1(seconds: int) -> None:
    """Set yogrt's "interval1" time.

    This is the time between checks of the remaining time, so long as
    the remaining time is greater than the "interval2_start" value.

    Args:
        seconds (int): The number of seconds to set the "interval1"
        time to.
    """
    _yogrt_c_lib.yogrt_set_interval1(seconds)


def set_interval2(seconds: int) -> None:
    """Set yogrt's "interval2" time.

    This is the time between checks of the remaining time used when
    there are fewer than "interval2_start" seconds remaining.

    Args:
        seconds (int): The number of seconds to set "interval2" to.
    """
    _yogrt_c_lib.yogrt_set_interval2(seconds)


def set_interval2_start(seconds: int) -> None:
    """Set yogrt's "interval2_start" time.

    This is the amount of remaining time after which yogrt switches to
    checking the remaining time every "interval2" seconds.

    Args:
        seconds (int): The number of seconds to set "interval2_start"
        to.
    """
    _yogrt_c_lib.set_interval2_start(seconds)


def get_interval1() -> int:
    """Get yogrt's "interval1" time."""
    return _yogrt_c_lib.yogrt_get_interval1()


def get_interval2() -> int:
    """Get yogrt's "interval2" time."""
    return _yogrt_c_lib.yogrt_get_interval2()


def get_interval2_start() -> int:
    """Get yogrt's "interval2_start" time."""
    return _yogrt_c_lib.yogrt_get_interval2_start()


def set_debug(val: int) -> None:
    """Set yogrt's internal debugging level.

    A value of 0 turns off debugging information. Values greater than
    0 will result in more verbose information being printed. Currently,
    the highest debug level is 3.

    Args:
        val (int): Debugging level to set.
    """
    _yogrt_c_lib.yogrt_set_debug(val)


def get_debug() -> int:
    """Get yogrt's current debugging level."""
    return _yogrt_c_lib.yogrt_get_debug()


# These methods are a newer libyogrt API:

if hasattr(_yogrt_c_lib, 'yogrt_init'):
    def init() -> None:
        """Initialize the yogrt library."""
        _yogrt_c_lib.yogrt_init()


    def fini() -> None:
        """Finalize the yogrt library."""
        _yogrt_c_lib.yogrt_fini()


    __all__ += ['init', 'fini']
