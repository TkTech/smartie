import ctypes
import os

from smartie.nvme import (
    NVMeDevice,
    NVMeResponse,
    local_byteorder,
)
from smartie.platforms.linux import get_libc
from smartie.nvme.structures import IOCTL_NVMe_ADMIN_CMD, NVMeAdminCommand


class LinuxNVMeDevice(NVMeDevice):
    """
    Represents an NVMe device on a Linux system.
    """

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

    def issue_admin_command(self, command: NVMeAdminCommand) -> NVMeResponse:
        result = get_libc().ioctl(
            self.fd, IOCTL_NVMe_ADMIN_CMD, ctypes.byref(command)
        )

        # Most commonly because the caller doesn't have root.
        if result < 0:
            raise OSError(f"NVMe Admin command failed with error {result}")

        # Status is in the upper 16 bits of the result
        status_field = self.parse_status_field(
            command.result.to_bytes(2, local_byteorder)
        )

        return NVMeResponse(
            succeeded=status_field.status_code == 0,
            command_spec=command.result,
            status_field=status_field,
            command=command,
            bytes_transferred=None,
            platform_header=None,
        )
