import ctypes
from typing import Union

from smartie.scsi import SCSIDevice, SCSIResponse
from smartie.platforms.win32 import get_kernel32
from smartie.scsi.structures import (
    Direction,
    IOCTL_SCSI_PASS_THROUGH_DIRECT,
    SCSIPassThroughDirect,
    SCSIPassThroughDirectWithBuffer,
)


class WindowsSCSIDevice(SCSIDevice):
    def __enter__(self):
        if self.fd is not None:
            raise IOError("Device is already open.")

        # We can't use the normal approach to opening a file on Windows, as
        # various Python APIs can't handle a device opened without specific
        # flags, see (https://bugs.python.org/issue37074)
        self.fd = get_kernel32().CreateFileW(
            self.path,
            0x80000000 | 0x40000000,  # GENERIC_READ | GENERIC_WRITE
            0x00000001,  # FILE_SHARE_READ
            None,
            0x00000003,  # OPEN_EXISTING
            0x00000080,  # FILE_ATTRIBUTE_NORMAL,
            None,
        )

        if self.fd == -1:
            raise ctypes.WinError(ctypes.get_last_error())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            get_kernel32().CloseHandle(self.fd)
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
        # On Windows, the command block is always 16 bytes, but we may be
        # sending a smaller command. We use a temporary mutable bytearray for
        # this.
        cdb = (ctypes.c_ubyte * 16).from_buffer_copy(
            bytearray(command).ljust(16, b"\x00")  # noqa
        )

        if data is None:
            data = ctypes.create_string_buffer(0)

        header_with_buffer = SCSIPassThroughDirectWithBuffer(
            sptd=SCSIPassThroughDirect(
                length=ctypes.sizeof(SCSIPassThroughDirect),
                data_in={
                    Direction.TO: 0,
                    Direction.FROM: 1,
                    Direction.NONE: 2,
                }.get(direction),
                data_transfer_length=ctypes.sizeof(data),
                data_buffer=ctypes.addressof(data),
                cdb_length=ctypes.sizeof(command),
                cdb=cdb,
                timeout_value=max(timeout // 1000, 1),
                sense_info_length=SCSIPassThroughDirectWithBuffer.sense.size,
                sense_info_offset=(
                    SCSIPassThroughDirectWithBuffer.sense.offset
                ),
            )
        )

        result = get_kernel32().DeviceIoControl(
            self.fd,
            IOCTL_SCSI_PASS_THROUGH_DIRECT,
            ctypes.pointer(header_with_buffer),
            ctypes.sizeof(header_with_buffer),
            ctypes.pointer(header_with_buffer),
            ctypes.sizeof(header_with_buffer),
            None,
            None,
        )

        self.parse_sense(bytearray(header_with_buffer.sense))

        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())

        return SCSIResponse(
            succeeded=(
                header_with_buffer.sptd.scsi_status == 0
                or header_with_buffer.sptd.scsi_status == 2
            ),
            sense=self.parse_sense(bytearray(header_with_buffer.sense)),
            platform_header=header_with_buffer,
            command=command,
            bytes_transferred=header_with_buffer.sptd.data_transfer_length,
        )
