__all__ = ('NVMEDevice',)
import abc
import ctypes
from abc import ABCMeta, abstractmethod

from smartie.device import Device
from smartie.nvme.structures import NVMEAdminCommand, NVMEAdminCommands, \
    NVMEIdentifyResponse


class NVMEDevice(Device, abc.ABC, metaclass=ABCMeta):
    @abstractmethod
    def issue_admin_command(self, command):
        pass

    def identify(self) -> NVMEIdentifyResponse:
        """
        Returns the parsed IDENTIFY results for CNS 01h, which contains
        the controller information.
        """
        data = NVMEIdentifyResponse()
        self.issue_admin_command(
            NVMEAdminCommand(
                opcode=NVMEAdminCommands.IDENTIFY,
                addr=ctypes.addressof(data),
                data_len=4096,
                cdw10=1,
            )
        )
        return data
