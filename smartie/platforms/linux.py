"""
Ancillary support functions for Linux.
"""

import ctypes
from functools import cache


@cache
def get_libc():
    # Opens the libc.so, which can be quite a slow process, and
    # saves it for future use.
    return ctypes.CDLL("libc.so.6", use_errno=True)
