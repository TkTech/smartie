__all__ = ("NVMeDevice", "NVMeResponse", "local_byteorder")
import abc
import sys
import ctypes
from dataclasses import dataclass
from abc import abstractmethod
from typing import Optional, Tuple, Union, Any

from smartie.device import Device
from smartie.nvme.errors import NVMeStatusFieldError
from smartie.nvme.structures import (
    NVMeAdminCommand,
    NVMeAdminCommands,
    NVMeIdentifyResponse,
    NVMeCQEStatusField,
    SMARTPageResponse,
)
from smartie.structures import structure_to_dict

local_byteorder = sys.byteorder


@dataclass
class NVMeResponse:
    """
    Common response object for NVMe commands.

    This object attempts to encapsulate the response from a NVMe command in a
    platform-agnostic way. It contains the Status Field, the command that was
    issued, command spec value and whether the command succeeded or not.

    For additional platform-specific information, the `platform_header`
    attribute contains the platform-specific header that was used to issue the
    command.
    """

    #: Whether the command succeeded. If None, the status is unknown.
    succeeded: Optional[bool]
    #: The Command Specific value returned by the device.
    #: The value maybe either of command error information or
    #: the wanted value return by no data transfer command
    command_spec: Optional[int]
    #: The status field data returned by the device.
    status_field: Optional[NVMeCQEStatusField]
    #: The command issued to the device.
    command: Union[NVMeAdminCommand,]
    #: Keep aligned with SCSIResponse. Not used for now.
    #: The actual number of bytes transferred.
    bytes_transferred: Optional[int]

    #: Keep aligned with SCSIResponse. Not used for now.
    #: The platform-specific header that was used to issue the command.
    #: For example this may be an :class:`SCSIPassThroughDirectWithBuffer` on
    #: Windows.
    platform_header: Any

    def __bool__(self):
        return self.succeeded


class NVMeDevice(Device, abc.ABC):
    @classmethod
    def parse_status_field(cls, status_blob) -> Optional[NVMeCQEStatusField]:
        """
        Parses the command status field from an NVMe command, raising a
        :class:`smartie.nvme.errors.NVMeStatusFieldError` if an error occurred.

        :param status_blob: A bytes/bytearray (or similar) object containing
                            the unparsed sense response.
        """
        status_field = NVMeCQEStatusField.from_buffer_copy(status_blob)
        if status_field.status_code != 0 or status_field.status_code_type != 0:
            raise NVMeStatusFieldError(
                status_field.status_code,
                status_field.status_code_type,
                status_field=status_field,
            )
        return status_field

    @abstractmethod
    def issue_admin_command(self, command):
        pass

    def identify(self) -> Tuple[NVMeIdentifyResponse, NVMeResponse]:
        """
        Returns the parsed IDENTIFY results for CNS 01h, which contains
        the controller information.
        """
        data = NVMeIdentifyResponse()
        response = self.issue_admin_command(
            NVMeAdminCommand(
                opcode=NVMeAdminCommands.IDENTIFY,
                addr=ctypes.addressof(data),
                data_len=ctypes.sizeof(data),
                cdw10=1,
            )
        )
        return data, response

    @property
    def serial(self) -> Optional[str]:
        identify, response = self.identify()
        return bytearray(identify.serial_number).strip(b" \x00").decode()

    @property
    def model(self) -> Optional[str]:
        identify, response = self.identify()
        return bytearray(identify.model_number).strip(b" \x00").decode()

    @property
    def temperature(self) -> Optional[int]:
        smart, response = self.smart()
        return int(smart.temperature - 273.15)

    def read_log_page(
        self, log_page_id: int, data: ctypes.Structure
    ) -> tuple[ctypes.Structure, NVMeResponse]:
        response = self.issue_admin_command(
            NVMeAdminCommand(
                opcode=NVMeAdminCommands.GET_LOG_PAGE,
                addr=ctypes.addressof(data),
                data_len=ctypes.sizeof(data),
                nsid=0xFFFFFFFF,
                cdw10=log_page_id | (((ctypes.sizeof(data) // 4) - 1) << 16),
            )
        )
        return data, response

    def smart(self):
        return self.read_log_page(0x02, SMARTPageResponse())

    @property
    def smart_table(self) -> dict[str, any]:
        smart, response = self.smart()
        return structure_to_dict(smart)
