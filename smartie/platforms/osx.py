"""
Ancillary support functions for OS X.
"""

import ctypes

iokit = ctypes.CDLL(
    "/System/Library/Frameworks/IOKit.framework/IOKit", use_errno=True
)

cf = ctypes.CDLL(
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation",
    use_errno=True,
)

kCFBooleanTrue = ctypes.c_void_p.in_dll(cf, "kCFBooleanTrue")

iokit.IOServiceMatching.restype = ctypes.c_void_p

iokit.IOServiceGetMatchingServices.restype = ctypes.c_int
iokit.IOServiceGetMatchingServices.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
]

iokit.IORegistryEntryCreateCFProperty.restype = ctypes.c_void_p
iokit.IORegistryEntryCreateCFProperty.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint32,
]

cf.CFStringCreateWithCString.restype = ctypes.c_void_p
cf.CFStringCreateWithCString.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.c_uint32,
]

cf.CFDictionaryAddValue.restype = None
cf.CFDictionaryAddValue.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
]
