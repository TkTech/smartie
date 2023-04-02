__all__ = ('NVMEDevice',)
import abc
import ctypes
from abc import ABCMeta, abstractmethod

from smartie.device import Device
from smartie.nvme.structures import (
    NVMEAdminCommand,
    NVMEAdminCommands,
    NVMEIdentifyResponse, SMARTPageResponse
)


class NVMEDevice(Device, abc.ABC):
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
                data_len=ctypes.sizeof(data),
                cdw10=1,
            )
        )
        return data

    @property
    def serial(self) -> str | None:
        identify = self.identify()
        return bytearray(identify.serial_number).strip(b' \x00').decode()

    @property
    def model(self) -> str | None:
        identify = self.identify()
        return bytearray(identify.model_number).strip(b' \x00').decode()

    @property
    def temperature(self) -> int | None:
        return int(self.smart().temperature - 273.15)

    def read_log_page(self, log_page_id: int, data: ctypes.Structure):
        self.issue_admin_command(
            NVMEAdminCommand(
                opcode=NVMEAdminCommands.GET_LOG_PAGE,
                addr=ctypes.addressof(data),
                data_len=ctypes.sizeof(data),
                nsid=0xFFFFFFFF,
                cdw10=log_page_id | (((ctypes.sizeof(data) // 4) - 1) << 16)
            )
        )
        return data

    def smart(self):
        return self.read_log_page(0x02, SMARTPageResponse())
