import ctypes


class NVMEAdminCommand(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('opcode', ctypes.c_ubyte),
        ('flags', ctypes.c_ubyte),
        ('reserved_1', ctypes.c_ushort),
        ('nsid', ctypes.c_uint32),
        ('cdw2', ctypes.c_uint32),
        ('cdw3', ctypes.c_uint32),
        ('metadata', ctypes.c_uint64),
        ('addr', ctypes.c_uint64),
        ('metadata_len', ctypes.c_uint32),
        ('data_len', ctypes.c_uint32),
        ('cdw10', ctypes.c_uint32),
        ('cdw11', ctypes.c_uint32),
        ('cdw12', ctypes.c_uint32),
        ('cdw13', ctypes.c_uint32),
        ('cdw14', ctypes.c_uint32),
        ('cdw15', ctypes.c_uint32),
        ('timeout_ms', ctypes.c_uint32),
        ('result', ctypes.c_uint32)
    ]


class NVMEIdentifyResponse(ctypes.Structure):
    _fields_ = [
        ('vid', ctypes.c_uint16),
        ('ssvid', ctypes.c_uint16),
        ('sn', ctypes.c_ubyte * 20),
        ('mn', ctypes.c_ubyte * 40),
        ('fr', ctypes.c_ubyte * 8),
    ]
