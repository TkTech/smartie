import ctypes


class c_uint128(ctypes.Structure):  # noqa
    _pack_ = 1
    _fields_ = [("low", ctypes.c_uint64), ("high", ctypes.c_uint64)]

    def __init__(self, value: int = 0):
        super().__init__()
        self.low = value & 0xFFFFFFFFFFFFFFFF
        self.high = (value >> 64) & 0xFFFFFFFFFFFFFFFF

    @property
    def value(self) -> int:
        return (self.high << 64) | self.low

    def __int__(self):
        return self.value

    def __format__(self, format_spec):
        return self.value.__format__(format_spec)
