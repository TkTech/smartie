import ctypes
from typing import Optional, Union

from smartie.scsi import SCSIDevice, SCSIResponse
from smartie.scsi.structures import Direction


class MockedSCSIDevice(SCSIDevice):
    def __init__(
        self,
        *args,
        return_data: Optional[bytes] = None,
        return_sense=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._return_data = return_data
        self._return_sense = return_sense

    def issue_command(
        self,
        direction: Direction,
        command: ctypes.Structure,
        data: Union[ctypes.Array, ctypes.Structure, None],
        *,
        timeout: int = 3000,
    ) -> SCSIResponse:
        if self._return_data:
            ctypes.memmove(data, self._return_data, len(self._return_data))

        return SCSIResponse(
            sense=self._return_sense,
            platform_header=None,
            bytes_transferred=len(self._return_data)
            if self._return_data
            else 0,
            succeeded=True,
            command=command,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
