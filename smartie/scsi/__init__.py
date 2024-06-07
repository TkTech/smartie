__all__ = ("SCSIDevice",)

import abc
import ctypes
from dataclasses import replace
from typing import Dict, List, Optional, Tuple, Union

import smartie.structures
from smartie import util
from smartie.database import SMARTAttribute, get_drive_entry
from smartie.device import Device
from smartie.errors import SenseError
from smartie.scsi.structures import (
    ATACommands,
    ATAPICommands,
    ATAProtocol,
    ATASmartFeature,
    Command16,
    CommandFlags,
    DescriptorFormatSense,
    DeviceType,
    Direction,
    FixedFormatSense,
    IdentifyResponse,
    InquiryCommand,
    InquiryResponse,
    OperationCode,
    SmartDataResponse,
    SmartThresholdResponse,
)
from smartie.structures import swap_bytes


class SCSIDevice(Device, abc.ABC):
    @classmethod
    def parse_sense(cls, sense_blob):
        """
        Parses the sense response from an SCSI command, raising a
        :class:`smartie.errors.SenseError` if an error occurred.

        Will return either a :class:`structures.FixedFormatSense` or a
        :class:`structures.DescriptorFormatSense` depending on the error code.

        :param sense_blob: A bytearray (or similar) object containing the
                           unparsed sense response.
        """
        error_code = sense_blob[0] & 0x7F
        if error_code == 0x00:
            return None
        elif error_code in (0x70, 0x71):
            sense = FixedFormatSense.from_buffer_copy(sense_blob)
            if sense.sense_key not in (0x00, 0x01, 0x0F):
                raise SenseError(sense.sense_key, sense=sense)
            return sense
        elif error_code in (0x72, 0x73):
            sense = DescriptorFormatSense.from_buffer_copy(sense_blob)
            if sense.sense_key not in (0x00, 0x01, 0x0F):
                raise SenseError(sense.sense_key, sense=sense)
            return sense
        else:
            raise SenseError(0, sense=sense_blob)

    def issue_command(
        self,
        direction: structures.Direction,
        command: ctypes.Structure,
        data: Union[ctypes.Array, ctypes.Structure, None],
        *,
        timeout: int = 3000,
    ):
        """
        Issues an SCSI passthrough command to the disk.

        :param direction: Direction for this command.
        :param command: Command to be sent to the device.
        :param data: Command data to be sent/received to/from the device.
        :param timeout: Timeout in milliseconds. Setting this to MAX_INT
                        results in no timeout.
        """
        raise NotImplementedError()

    def inquiry(self):
        """
        Issues an SCSI INQUIRY command and returns a tuple of (result, sense).
        """
        inquiry = InquiryResponse()

        inquiry_command = InquiryCommand(
            operation_code=OperationCode.INQUIRY, allocation_length=96
        )

        sense = self.issue_command(Direction.FROM, inquiry_command, inquiry)

        return inquiry, sense

    def identify(self, try_atapi_on_failure=True):
        """
        Issues an ATA IDENTIFY command and returns a tuple of (result, sense).
        """
        identity = ctypes.create_string_buffer(b"\x00", 512)

        command16 = Command16(
            operation_code=OperationCode.COMMAND_16,
            protocol=ATAProtocol.PIO_DATA_IN << 1,
            flags=CommandFlags(
                t_length=CommandFlags.Length.IN_SECTOR_COUNT,
                byt_blok=True,
                t_dir=True,
                ck_cond=True,
            ),
            command=ATACommands.IDENTIFY,
        )

        try:
            sense = self.issue_command(Direction.FROM, command16, identity)
        except SenseError as err:
            # If an error occurred, we try to see if this is really an ATAPI
            # device, such as a CD-ROM. We can handle the response exactly
            # the same, it's just a different command.
            if not try_atapi_on_failure:
                raise

            command16.command = ATAPICommands.IDENTIFY
            sense = self.issue_command(Direction.FROM, command16, identity)

        return IdentifyResponse.from_buffer(identity), sense

    @property
    def model(self) -> Optional[str]:
        """
        Returns the model name of the device.
        """
        identity, sense = self.identify()
        v = swap_bytes(identity.model_number).strip(b" \x00").decode()
        # If we didn't get anything at all back from an ATA IDENTIFY, try an
        # old fashion SCSI INQUIRY.
        if not v:
            inquiry, sense = self.inquiry()
            v = (
                bytearray(inquiry.product_identification)
                .strip(b" \x00")
                .decode()
            )
        return v

    @property
    def serial(self) -> Optional[str]:
        """
        Returns the serial number of the device.
        """
        identity, sense = self.identify()
        v = swap_bytes(identity.serial_number).strip(b" \x00").decode()
        # If we didn't get anything at all back from an ATA IDENTIFY, try an
        # old fashion SCSI INQUIRY.
        if not v:
            inquiry, sense = self.inquiry()
            v = bytearray(inquiry.vendor_specific_1).strip(b" \x00").decode()
        return v

    @property
    def temperature(self) -> Optional[int]:
        """
        Returns the temperature of the device in degrees Celsius.
        """
        smart_table = self.smart_table

        temp = smart_table.get(0xBE)
        if temp is not None:
            return temp.p_value

        temp = smart_table.get(0xC2)
        if temp is not None:
            return temp.p_value

    @property
    def device_type(self):
        """
        Get the device's type, if available.
        """
        inquiry, sense = self.inquiry()
        return DeviceType(inquiry.peripheral_device_type)

    def smart_thresholds(self) -> Tuple[SmartThresholdResponse, SenseError]:
        """
        Issues an ATA SMART READ_THRESHOLDS command and returns a tuple of
        (result, sense).
        """
        thresholds = SmartThresholdResponse()

        command16 = Command16(
            operation_code=OperationCode.COMMAND_16,
            protocol=ATAProtocol.PIO_DATA_IN << 1,
            command=ATACommands.SMART,
            flags=CommandFlags(
                t_length=CommandFlags.Length.IN_SECTOR_COUNT,
                byt_blok=True,
                t_dir=True,
                ck_cond=True,
            ),
            features=smartie.structures.swap_int(
                2, ATASmartFeature.SMART_READ_THRESHOLDS
            ),
        ).set_lba(0xC24F00)

        sense = self.issue_command(Direction.FROM, command16, thresholds)
        return thresholds, sense

    def smart(self) -> Tuple[SmartDataResponse, SenseError]:
        """
        Issues an ATA SMART READ_DATA command and returns a tuple of
        (result, sense).
        """
        smart = SmartDataResponse()

        command16 = Command16(
            operation_code=OperationCode.COMMAND_16,
            protocol=ATAProtocol.PIO_DATA_IN << 1,
            command=ATACommands.SMART,
            flags=CommandFlags(
                t_length=CommandFlags.Length.IN_SECTOR_COUNT,
                byt_blok=True,
                t_dir=True,
                ck_cond=True,
            ),
            features=smartie.structures.swap_int(
                2, ATASmartFeature.SMART_READ_DATA
            ),
        ).set_lba(0xC24F00)

        sense = self.issue_command(Direction.FROM, command16, smart)
        return smart, sense

    def get_filters(self) -> List[str]:
        return ["type:ata", f"model:{self.model}"]

    @property
    def smart_table(self) -> Dict[int, SMARTAttribute]:
        """
        Returns a parsed and processed dictionary of SMART attributes.
        """
        drive_entry = get_drive_entry(self.get_filters())

        thresholds, _ = self.smart_thresholds()
        p_thresholds = {}
        for entry in thresholds.entries:
            if entry.attribute_id == 0x00:
                break
            p_thresholds[entry.attribute_id] = entry.value

        smart, _ = self.smart()
        result = {}
        for entry in smart.attributes:
            if entry.id == 0x00:
                break

            result[entry.id] = replace(
                drive_entry.smart_attributes.get(
                    entry.id,
                    SMARTAttribute(
                        "UNKNOWN",
                        id=entry.id,
                        flags=entry.flags,
                        current_value=entry.current,
                        worst_value=entry.worst,
                        threshold=p_thresholds.get(entry.id),
                    ),
                ),
                flags=entry.flags,
                current_value=entry.current,
                worst_value=entry.worst,
                threshold=p_thresholds.get(entry.id),
            )

        return result
