import ctypes
import os

from smartie.nvme import NVMEDevice
from smartie.platforms.linux import get_libc
from smartie.nvme.structures import IOCTL_NVME_ADMIN_CMD, NVMEAdminCommand


class LinuxNVMEDevice(NVMEDevice):
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

    def issue_admin_command(self, command: NVMEAdminCommand):
        result = get_libc().ioctl(
            self.fd, IOCTL_NVME_ADMIN_CMD, ctypes.byref(command)
        )

        if result != 0:
            raise OSError(ctypes.get_errno())
