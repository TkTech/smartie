from smartie.nvme.constants import NVMe_STATUS_FIELD


class NVMeStatusFieldError(Exception):
    """
    Raised when an NVMe command returns an error status field.
    """

    def __init__(
        self,
        status_code: int,
        status_code_type: int,
        *,
        status_field=None,
    ):
        super().__init__()
        #: The status code.
        self.status_code = status_code
        #: The status code type.
        self.status_code_type = status_code_type
        #: The status field structure, if available.
        self.status_filed = status_field

    @property
    def error_msg(self) -> str:
        return NVMe_STATUS_FIELD.get(
            (self.status_code_type, self.status_code),
            "Unknown Error",
        )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"status_code_type=0x{self.status_code_type:02x},"
            f" status_code=0x{self.status_code:02x},"
            f" err={self.error_msg!r}"
            f")>"
        )
