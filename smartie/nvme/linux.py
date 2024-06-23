import ctypes
import os

from smartie.nvme import (
    NVMEDevice,
    NVMeResponse,
    local_byteorder,
)
from smartie.platforms.linux import get_libc
from smartie.nvme.structures import IOCTL_NVME_ADMIN_CMD, NVMEAdminCommand


class LinuxNVMEDevice(NVMEDevice):
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

    def issue_admin_command(self, command: NVMEAdminCommand) -> NVMeResponse:
        result = get_libc().ioctl(
            self.fd, IOCTL_NVME_ADMIN_CMD, ctypes.byref(command)
        )

        return NVMeResponse(
            succeeded=(result == 0),
            command_spec=command.result,
            status_field=self.parse_status_field(
                result.to_bytes(2, byteorder=local_byteorder)
            ),
            command=command,
            bytes_transferred=None,
            platform_header=None,
        )
