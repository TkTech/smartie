"""
The various enums and constants encountered in the specs.
"""
import enum


#: The Linux IOCTL for SG_IO, which is the driver we use to send and receive
#: SCSI commands.
IOCTL_SG_IO = 0x2285
#: The Windows IOCTL for SCSI pass-through, which is what we use to send and
#: receive SCSI commands.
IOCTL_SCSI_PASS_THROUGH_DIRECT = 0x4D014


class DeviceType(enum.IntEnum):
    """
    Common device types returned by the SCSI INQUIRY command.

    .. note::

        Not all possible values are defined here due to lack of testable
        hardware.
    """
    #: Direct access block device (ex: disk)
    DIRECT_ACCESS_BLOCK_DEVICE = 0x00
    #: Sequential access device (ex: tape drive)
    SEQUENTIAL_ACCESS_DEVICE = 0x01
    #: CD/DVD/BLU-RAY
    CDROM = 0x05
    #: Some types of optical disks
    OPTICAL_MEMORY_DEVICE = 0x07
    #: Storage array controller device
    RAID_CONTROLLER = 0x0C
    #: Optical card reader/writer device
    OPTICAL_CARD_RW = 0x0F


class OperationCode(enum.IntEnum):
    #: SCSI INQUIRY command.
    INQUIRY = 0x12
    #: 16-byte ATA passthrough command.
    COMMAND_16 = 0x85
    #: 12-byte ATA passthrough command.
    COMMAND_12 = 0xA1


class ATAProtocol(enum.IntEnum):
    """
    The possible values for `Command16.protocol`.
    """
    HARD_RESET = 0
    SRST = 1
    NON_DATA = 3
    PIO_DATA_IN = 4
    PIO_DATA_OUT = 5
    DMA = 6
    DMA_QUEUED = 7
    DEVICE_DIAGNOSTIC = 8
    DEVICE_RESET = 9
    UDMA_DATA_IN = 10
    UDMA_DATA_OUT = 11
    FPDMA = 12
    RETURN_RESPONSE_INFORMATION = 15


class ATACommands(enum.IntEnum):
    """
    The possible values for `Command16.command`.
    """
    SMART = 0xB0
    IDENTIFY = 0xEC
    READ_DATA = 0xD0
    READ_LOG = 0xD5
    RETURN_STATUS = 0xDA


class ATAPICommands(enum.IntEnum):
    """
    The possible values for `Command16.command` when targeting an ATAPI device.
    """
    IDENTIFY = 0xA1


class StatusCode(enum.IntEnum):
    """
    The possible values for `SGIOHeader.status`.
    """
    GOOD = 0x00
    CHECK_CONDITION = 0x01
    CONDITION_GOOD = 0x02
    BUSY = 0x04
    INTERMEDIATE_GOOD = 0x08
    INTERMEDIATE_C_GOOD = 0x0A
    RESERVATION_CONFLICT = 0x0C


class SenseErrorCode(enum.IntEnum):
    CURRENT_ERROR = 0x70
    DEFERRED_ERROR = 0x71


class Direction(enum.IntEnum):
    """
    The direction of the command being sent by a call to
    DeviceIO.issue_command.

    .. note::

        These are really the constants for the direction in SG_IO calls, but we
        map them for other platforms.
    """
    TO = -2
    FROM = -3


class ATASmartFeature(enum.IntEnum):
    """
    The possible values for the `feature` field on an ATA SMART command.
    """
    SMART_READ_DATA = 0xD0
    SMART_READ_THRESHOLDS = 0xD1
    SMART_TOGGLE_ATTRIBUTE_AUTOSAVE = 0xD2
    SMART_EXECUTE_OFF_LINE_IMMEDIATE = 0xD4
    SMART_READ_LOG = 0xD5
    SMART_WRITE_LOG = 0xD6
    SMART_ENABLE_OPERATIONS = 0xD8
    SMART_DISABLE_OPERATIONS = 0xD9
    SMART_RETURN_STATUS = 0xDA
