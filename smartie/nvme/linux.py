import ctypes
import os

import smartie.nvme.constants
from smartie.nvme import NVMEDevice
from smartie.platforms.linux import get_libc
from smartie.nvme.structures import NVMEAdminCommand


class LinuxNVMEDevice(NVMEDevice):
    def __enter__(self):
        if self.fd is not None:
            raise IOError('Device already open.')

        self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        return False

    def issue_admin_command(self, command: NVMEAdminCommand):
        result = get_libc().ioctl(
            self.fd,
            smartie.nvme.constants.IOCTL_NVME_ADMIN_CMD,
            ctypes.byref(command)
        )

        if result != 0:
            raise OSError(ctypes.get_errno())

    @property
    def model(self) -> str | None:
        identify = self.identify()
        return bytearray(identify.mn).strip(b' \x00').decode()

    @property
    def serial(self) -> str | None:
        identify = self.identify()
        return bytearray(identify.sn).strip(b' \x00').decode()
