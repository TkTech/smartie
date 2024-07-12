import ctypes
from typing import Union
from smartie.platforms.win32 import get_kernel32
from smartie.nvme import (
    NVMeDevice,
    NVMeResponse,
    local_byteorder,
)
from smartie.nvme.structures import (
    NVMeAdminCommand, 
    NVMeAdminCommands,
    StoragePropertyQuery,
    StorageProtocolSpecificData,
    NVMeSpecificDataQueryHeader,
    GetNVMeSpecificDataQueryWithData,
    StorageProtocolSpecificData,
    STORAGE_PROTOCOL_DATA_DESCRIPTOR,
    BytesReturnedStruc,
)

##
NVME_MAX_LOG_SIZE = 0x1000
##

class WindowsNVMeDevice(NVMeDevice):
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

    def issue_admin_command(self, command: NVMeAdminCommand) -> NVMeResponse:
        # Now only support get log page,identify command.
        # From https://learn.microsoft.com/en-us/windows/win32/fileio/working-with-nvme-devices
        # and nvme spec 1.4c.
        # Now transfer the linux-type command to windows-type
        # define a command specific "Validate the returned data" functions
        def _check_returned_data():
            return True
        # 0,   data from host to device
        # 1, data from device to host
        # 2, non data transfer
        direction = 2 # default none data transfer
        if command.opcode in (NVMeAdminCommands.GET_LOG_PAGE.value, 
                              NVMeAdminCommands.IDENTIFY.value):
            direction = 1
            property_query = StoragePropertyQuery()
            protocol_specific_data = StorageProtocolSpecificData()
            # common settings
            property_query.QueryType = 0      # PropertyStandardQuery
            protocol_specific_data.ProtocolType = 0x03 # ProtocolTypeNvme
            protocol_specific_data.ProtocolDataOffset = ctypes.sizeof(StorageProtocolSpecificData)
            protocol_specific_data.ProtocolDataLength = command.data_len
            # specific settings
            if command.opcode == NVMeAdminCommands.GET_LOG_PAGE.value:   # Get Log page
                property_query.PropertyId = 0x32  # StorageDeviceProtocolSpecificProperty
                protocol_specific_data.DataType = 0x02 # NVMeDataTypeLogPage
                protocol_specific_data.ProtocolDataRequestValue = command.cdw10 & 0xFF  # Log Page Identifier (LID)
                protocol_specific_data.ProtocolDataRequestSubValue = command.cdw12
                protocol_specific_data.ProtocolDataRequestSubValue2 = command.cdw13
                protocol_specific_data.ProtocolDataRequestSubValue3 = (command.cdw11 >> 16) & 0xFFFF  # Log Specific Identifier
                protocol_specific_data.ProtocolDataRequestSubValue4 = (   # user can pass Retain Asynchronous Event, Log Specific Field
                    (command.cdw10 >> 15) & 0x01 +               # bit 0: Retain Asynchronous Event (RAE)
                    ((command.cdw10 >> 8) & 0x0F) << 1           # bit 1-4: Log Specific Field (LSP)
                )
            elif command.opcode == NVMeAdminCommands.IDENTIFY.value: # Identify
                property_query.PropertyId = 0x31  # StorageAdapterProtocolSpecificProperty
                protocol_specific_data.DataType = 0x01 # NVMeDataTypeIdentify
                protocol_specific_data.ProtocolDataRequestValue = command.cdw10 & 0xFF  # Controller or Namespace Structure (CNS):
            # ! Important !
            # For an IOCTL_STORAGE_QUERY_PROPERTY that uses a STORAGE_PROPERTY_ID of StorageAdapterProtocolSpecificProperty, 
            # and whose STORAGE_PROTOCOL_SPECIFIC_DATA or STORAGE_PROTOCOL_SPECIFIC_DATA_EXT structure is set to ProtocolType=ProtocolTypeNvme 
            # and DataType=NVMeDataTypeLogPage, set the ProtocolDataLength member of that same structure to a minimum value of 512 (bytes).
            if (
                property_query.PropertyId == 0x31
                and protocol_specific_data.DataType == 0x02
            ):
                # For now, it will never go into here, just a hint
                raise
            command_header = NVMeSpecificDataQueryHeader(
                storage_property_query=property_query,
                storage_protocol_specific_data=protocol_specific_data,
            )
            # the needed structures
            raw_cdb = GetNVMeSpecificDataQueryWithData(command.data_len)(command_header=command_header)
            IOCTL_Request = 0x2D1400 # NVMe Admin Command
            # rewrite the _check_returned_data()
            def _check_returned_data():
                protocolDataDescr = STORAGE_PROTOCOL_DATA_DESCRIPTOR.from_buffer_copy(bytearray(command_header))
                if (protocolDataDescr.Version != ctypes.sizeof(STORAGE_PROTOCOL_DATA_DESCRIPTOR)
                    or protocolDataDescr.Size != ctypes.sizeof(STORAGE_PROTOCOL_DATA_DESCRIPTOR)
                    ):
                    # DeviceNVMeQueryProtocolDataTest: data descriptor header not valid.
                    return False
                if (
                    protocolDataDescr.storage_protocol_specific_data.ProtocolDataOffset < ctypes.sizeof(StorageProtocolSpecificData)
                    or protocolDataDescr.storage_protocol_specific_data.ProtocolDataLength < command.data_len
                ):
                    # DeviceNVMeQueryProtocolDataTest: ProtocolData Offset/Length not valid.
                    return False
                return True
        else:
            raise NotImplementedError("Command Not Implemented: opcode %#x" % command.opcode)
        # send request down
        return_bytes = BytesReturnedStruc(return_bytes=0)
        result = get_kernel32().DeviceIoControl(
            self.fd,
            IOCTL_Request,
            ctypes.pointer(raw_cdb),
            ctypes.sizeof(raw_cdb),
            ctypes.pointer(raw_cdb),
            ctypes.sizeof(raw_cdb),
            ctypes.pointer(return_bytes),
            None,
        )

        # How to check if a command succeeded?
        # TODO, I don't know how to check the status filed in this structure for now, it should be raised in result != 0 if command failed 
        # Need more?
        # the windows should check if data returned is valid, it should be checked by _check_returned_data()
        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        # command success, it should be always 0 here
        status_field = 0
        # set the valid data back to command if the command read data from device,
        # because the reference may take the data in command.
        if direction == 1:
            ctypes.memmove(command.addr, raw_cdb.data, command.data_len)
        return NVMeResponse(
            succeeded=(result == 0 and _check_returned_data()),
            command_spec=protocol_specific_data.FixedProtocolReturnData,
            status_field=self.parse_status_field(
                status_field.to_bytes(2, byteorder=local_byteorder)
            ),
            command=raw_cdb,
            bytes_transferred=int.from_bytes(bytes(return_bytes), local_byteorder) - len(bytes(command_header)), # the actual bytes transfer
            platform_header=command_header,
        )
