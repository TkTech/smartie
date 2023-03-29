import ctypes
import os

import smartie.nvme.constants
from smartie.scsi import constants
from smartie.nvme import NVMEDevice
from smartie._linux import _get_libc
from smartie.nvme.structures import NVMEAdminCommand, NVMEIdentifyResponse


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
        result = _get_libc().ioctl(
            self.fd,
            smartie.nvme.constants.IOCTL_NVME_ADMIN_CMD,
            ctypes.byref(command)
        )

        if result != 0:
            raise OSError(ctypes.get_errno())

    def identify_controller(self) -> NVMEIdentifyResponse:
        """
        Returns the parsed IDENTIFY results for CNS 01h, which contains
        the controller information.
        """
        data = ctypes.create_string_buffer(b'\x00', 4096)
        self.issue_admin_command(
            NVMEAdminCommand(
                opcode=smartie.nvme.constants.NVMEAdminCommand.IDENTIFY,
                addr=ctypes.addressof(data),
                data_len=4096,
                cdw10=1,
            )
        )
        return NVMEIdentifyResponse.from_buffer(data)

    @property
    def model(self) -> str | None:
        identify = self.identify_controller()
        return bytearray(identify.mn).strip(b' \x00').decode()

    @property
    def serial(self) -> str | None:
        identify = self.identify_controller()
        return bytearray(identify.sn).strip(b' \x00').decode()
