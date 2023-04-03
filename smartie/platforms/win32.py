import ctypes
from functools import cache


@cache
def get_kernel32():
    # Opens the Kernel32.dll, which can be quite a slow process, and
    # saves it for future use.
    return ctypes.WinDLL("kernel32", use_last_error=True)
