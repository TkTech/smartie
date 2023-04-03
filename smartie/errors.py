class SenseError(Exception):
    def __init__(self, error_code: int, *, sense=None):
        super().__init__()
        self.error_code = error_code
        self.sense = sense

    @property
    def error_msg(self) -> str:
        return {
            0x00: "No Sense",
            0x01: "Recovered Error",
            0x02: "Not Ready",
            0x03: "Medium Error",
            0x04: "Hardware Error",
            0x05: "Illegal Request",
            0x06: "Unit Attention",
            0x07: "Data Protect",
            0x09: "Firmware Error",
            0x0B: "Aborted Command",
            0x0C: "Equal",
            0x0D: "Volume Overflow",
            0x0E: "Miscompare",
            0x0F: "Completed",
        }.get(self.error_code, "Unknown Sense Error")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}(error_code=0x{self.error_code:02x},"
            f" err={self.error_msg!r})>"
        )

    __str__ = __repr__
