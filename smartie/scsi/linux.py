import ctypes
import os
from typing import Union

from smartie.scsi import SCSIDevice, SCSIResponse
from smartie.platforms.linux import get_libc
from smartie.scsi.structures import (
    DescriptorFormatSense,
    FixedFormatSense,
    IOCTL_SG_IO,
    SGIOHeader,
    Direction,
    StatusCode,
)


class LinuxSCSIDevice(SCSIDevice):
    def __enter__(self):
        if self.fd is not None:
            raise IOError("Device already open.")

        self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        return False

    def issue_command(
        self,
        direction: Direction,
        command: ctypes.Structure,
        data: Union[ctypes.Array, ctypes.Structure, None],
        *,
        timeout: int = 3000,
    ) -> SCSIResponse:
        # The Sense response can be in multiple formats, and we won't know
        # what it is until we see the first byte.
        raw_sense = ctypes.create_string_buffer(
            b"\x00",
            max(
                ctypes.sizeof(FixedFormatSense),
                ctypes.sizeof(DescriptorFormatSense),
            ),
        )

        if data is None:
            data = ctypes.create_string_buffer(0)

        sg_io_header = SGIOHeader(
            interface_id=83,  # Always 'S'
            dxfer_direction=direction,
            cmd_len=ctypes.sizeof(command),
            cmdp=ctypes.addressof(command),
            dxfer_len=ctypes.sizeof(data),
            dxferp=ctypes.addressof(data),
            mx_sb_len=ctypes.sizeof(raw_sense),
            sbp=ctypes.addressof(raw_sense),
            timeout=timeout,
        )

        # We use libc instead of the builtin ioctl as the builtin can have
        # issues with 64-bit pointers.
        result = get_libc().ioctl(
            self.fd, IOCTL_SG_IO, ctypes.byref(sg_io_header)
        )

        if result != 0:
            raise OSError(ctypes.get_errno())

        return SCSIResponse(
            succeeded=(
                sg_io_header.status == StatusCode.GOOD
                or sg_io_header.status == StatusCode.CONDITION_GOOD
            ),
            sense=self.parse_sense(raw_sense.raw),
            platform_header=sg_io_header,
            command=command,
            bytes_transferred=sg_io_header.dxfer_len - sg_io_header.resid,
        )
