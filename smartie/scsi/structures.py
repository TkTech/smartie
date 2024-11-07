"""
This file contains the various low-level structure definitions used for sending
and receiving SCSI commands, as well as the structures required for
platform-specific APIs.

Where reasonable, the names of fields have been taken from the specifications
to ease reference searches.
"""

import ctypes
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

    NONE = -1
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


class InquiryCommand(ctypes.Structure):
    """
    An SCSI INQUIRY command.
    """

    _pack_ = 1
    _fields_ = [
        ("operation_code", ctypes.c_ubyte),
        ("lun", ctypes.c_ubyte),
        ("page_code", ctypes.c_ubyte),
        ("reserved_1", ctypes.c_ubyte),
        ("allocation_length", ctypes.c_ubyte),
        ("control", ctypes.c_ubyte),
    ]


class InquiryResponse(ctypes.Structure):
    """
    The response to an SCSI INQUIRY command.
    """

    _pack_ = 1
    _fields_ = [
        ("peripheral_device_type", ctypes.c_ubyte, 4),
        ("peripheral_qualifier", ctypes.c_ubyte, 4),
        ("reserved_1", ctypes.c_ubyte, 4),
        ("hot_pluggable", ctypes.c_ubyte, 2),
        ("lu_cong", ctypes.c_ubyte, 1),
        ("rmb", ctypes.c_ubyte, 1),
        ("version", ctypes.c_ubyte),
        ("response_data_format", ctypes.c_ubyte, 4),
        ("hi_sup", ctypes.c_ubyte, 1),
        ("norm_aca", ctypes.c_ubyte, 1),
        ("reserved_2", ctypes.c_ubyte, 1),
        ("reserved_3", ctypes.c_ubyte, 1),
        ("additional_length", ctypes.c_ubyte),
        ("protect", ctypes.c_ubyte, 1),
        ("reserved_4", ctypes.c_ubyte, 2),
        ("three_pc", ctypes.c_ubyte, 1),
        ("tpgs", ctypes.c_ubyte, 1),
        ("obsolete_1", ctypes.c_ubyte, 1),
        ("sccs", ctypes.c_ubyte, 1),
        ("obsolete_2", ctypes.c_ubyte, 1),
        ("reserved_5", ctypes.c_ubyte, 1),
        ("reserved_6", ctypes.c_ubyte, 1),
        ("obsolete_3", ctypes.c_ubyte, 1),
        ("multi_p", ctypes.c_ubyte, 1),
        ("vs_1", ctypes.c_ubyte, 1),
        ("enc_serv", ctypes.c_ubyte, 1),
        ("obsolete_4", ctypes.c_ubyte, 1),
        ("vs_2", ctypes.c_ubyte, 1),
        ("cmd_que", ctypes.c_ubyte, 1),
        ("reserved_7", ctypes.c_ubyte, 1),
        ("obsolete_5", ctypes.c_ubyte, 1),
        ("obsolete_6", ctypes.c_ubyte, 2),
        ("reserved_8", ctypes.c_ubyte, 1),
        ("obsolete_7", ctypes.c_ubyte, 1),
        ("t10_vendor_identification", ctypes.c_ubyte * 8),
        ("product_identification", ctypes.c_ubyte * 16),
        ("product_revision_level", ctypes.c_ubyte * 4),
        ("vendor_specific_1", ctypes.c_ubyte * 20),
        ("obsolete_8", ctypes.c_ubyte, 4),
        ("reserved_9", ctypes.c_ubyte, 4),
        ("reserved_10", ctypes.c_ubyte),
        ("version_descriptors", ctypes.c_ushort * 16),
        ("reserved_11", ctypes.c_ubyte * 22),
    ]


class CommandFlags(ctypes.Structure):
    """
    The flags used in the SCSI Command16 and Command12 structures.
    """

    class Length(enum.IntEnum):
        """
        Possible values for the `t_length` field.
        """

        #: The transfer length is in the FEATURE field.
        IN_FEATURE = 0b01
        #: The transfer length is in the SECTOR_COUNT field.
        IN_SECTOR_COUNT = 0b10
        #: The transfer length is in the STPIU.
        IN_STPSIU = 0b11

    class OffLine(enum.IntFlag):
        """
        Possible values for the `off_line` field.
        """

        ZERO_SECONDS = 0b00
        TWO_SECONDS = 0b01
        SIX_SECONDS = 0b10
        FOURTEEN_SECONDS = 0b11

    _pack_ = 1
    _fields_ = [
        # If set, determines how the transfer length is specified.
        ("t_length", ctypes.c_ubyte, 2),
        # 0 if the t_length is in bytes, 1 if the t_length is in blocks.
        # Ignored if t_length is 0.
        ("byt_blok", ctypes.c_ubyte, 1),
        # If set to 0, the transfer is from the client to the ATA device.
        # If set to 1, the transfer is from the ATA device to the client.
        ("t_dir", ctypes.c_ubyte, 1),
        ("reserved_1", ctypes.c_ubyte, 1),
        # If set, the ATA device will copy the ATA register information to the
        # sense data even when no error occurs.
        ("ck_cond", ctypes.c_ubyte, 1),
        # The number of seconds to wait for the device to become ready after
        # issuing an ATA command to a PATA device that may cause it to be in
        # an unusable state.
        ("off_line", ctypes.c_ubyte, 2),
    ]


class Command12(ctypes.Structure):
    """
    A 12-byte SCSI/ATA passthrough command.

    .. note::

        The contents of this structure are documented in 04-262r8.pdf, section
        13.2.2.
    """

    _pack_ = 1
    _fields_ = [
        ("operation_code", ctypes.c_ubyte),
        ("protocol", ctypes.c_ubyte),
        ("flags", CommandFlags),
        ("features", ctypes.c_ubyte),
        ("reserved_1", ctypes.c_ubyte, 1),
        ("sector_count", ctypes.c_ubyte, 7),
        ("reserved_2", ctypes.c_ubyte, 1),
        ("lba_low", ctypes.c_ubyte, 7),
        ("reserved_3", ctypes.c_ubyte, 1),
        ("lba_mid", ctypes.c_ubyte, 7),
        ("reserved_4", ctypes.c_ubyte, 1),
        ("lba_high", ctypes.c_ubyte, 7),
        ("device", ctypes.c_ubyte),
        ("command", ctypes.c_ubyte),
        ("reserved_5", ctypes.c_ubyte),
        ("control", ctypes.c_ubyte),
    ]


class Command16(ctypes.Structure):
    """
    A 16-byte SCSI/ATA passthrough command.

    .. note::

        The contents of this structure are documented in 04-262r8.pdf, section
        13.2.3.
    """

    _pack_ = 1
    _fields_ = [
        ("operation_code", ctypes.c_ubyte),
        ("protocol", ctypes.c_ubyte),
        ("flags", CommandFlags),
        ("features", ctypes.c_ushort),
        ("sector_count", ctypes.c_ushort),
        ("lba_high_low", ctypes.c_ubyte),
        ("lba_low", ctypes.c_ubyte),
        ("lba_high_mid", ctypes.c_ubyte),
        ("lba_mid", ctypes.c_ubyte),
        ("lba_high_high", ctypes.c_ubyte),
        ("lba_high", ctypes.c_ubyte),
        ("device", ctypes.c_ubyte),
        ("command", ctypes.c_ubyte),
        ("control", ctypes.c_ubyte),
    ]

    def set_lba(self, lba: int):
        lba = lba.to_bytes(6, byteorder="little")
        self.lba_high_low = lba[3]
        self.lba_low = lba[0]
        self.lba_high_mid = lba[4]
        self.lba_mid = lba[1]
        self.lba_high_high = lba[5]
        self.lba_high = lba[2]

        return self


class SGIOHeader(ctypes.Structure):
    """
    Corresponds to the compat_sg_io_hdr structure in <scsi/sg.h> on Linux.
    """

    _fields_ = [
        ("interface_id", ctypes.c_int),
        ("dxfer_direction", ctypes.c_int),
        ("cmd_len", ctypes.c_ubyte),
        ("mx_sb_len", ctypes.c_ubyte),
        ("iovec_count", ctypes.c_ushort),
        ("dxfer_len", ctypes.c_uint),
        ("dxferp", ctypes.c_void_p),
        ("cmdp", ctypes.c_void_p),
        ("sbp", ctypes.c_void_p),
        ("timeout", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("pack_id", ctypes.c_int),
        ("usr_ptr", ctypes.c_void_p),
        ("status", ctypes.c_ubyte),
        ("masked_status", ctypes.c_ubyte),
        ("msg_status", ctypes.c_ubyte),
        ("sb_len_wr", ctypes.c_ubyte),
        ("host_status", ctypes.c_ushort),
        ("driver_status", ctypes.c_ushort),
        ("resid", ctypes.c_int),
        ("duration", ctypes.c_uint),
        ("info", ctypes.c_uint),
    ]


class SCSIPassThroughDirect(ctypes.Structure):
    """
    Corresponds to the SCSI_PASS_THROUGH_DIRECT structure in <ntddscsi.h> on
    Windows.
    """

    _fields_ = [
        ("length", ctypes.c_ushort),
        ("scsi_status", ctypes.c_ubyte),
        ("path_id", ctypes.c_ubyte),
        ("target_id", ctypes.c_ubyte),
        ("lun", ctypes.c_ubyte),
        ("cdb_length", ctypes.c_ubyte),
        ("sense_info_length", ctypes.c_ubyte),
        ("data_in", ctypes.c_ubyte),
        ("data_transfer_length", ctypes.c_uint32),
        ("timeout_value", ctypes.c_uint32),
        ("data_buffer", ctypes.c_void_p),
        ("sense_info_offset", ctypes.c_uint32),
        ("cdb", ctypes.c_ubyte * 16),
    ]


class SCSIPassThroughDirectWithBuffer(ctypes.Structure):
    """
    Corresponds to the SCSI_PASS_THROUGH_DIRECT_WITH_BUFFER structure in
    <ntddscsi.h> on Windows.
    """

    _fields_ = [
        ("sptd", SCSIPassThroughDirect),
        ("filler", ctypes.c_uint32),
        ("sense", ctypes.c_ubyte * 32),
    ]


class FixedFormatSense(ctypes.Structure):
    """
    The SENSE response may be in of two formats - this one, or
    :class:`DescriptorFormatSense`. The exact format depends on the value of
    the first byte, `error_code`.
    """

    _fields_ = [
        ("error_code", ctypes.c_ubyte, 7),
        ("valid", ctypes.c_ubyte, 1),
        ("segment_number", ctypes.c_ubyte),
        ("sense_key", ctypes.c_ubyte, 4),
        ("reserved_1", ctypes.c_ubyte, 1),
        ("ili", ctypes.c_ubyte, 1),
        ("eom", ctypes.c_ubyte, 1),
        ("filemark", ctypes.c_ubyte, 1),
        ("information", ctypes.c_uint32),
        ("additional_sense_length", ctypes.c_ubyte),
        ("command_specific_information", ctypes.c_uint32),
        ("additional_sense_code", ctypes.c_ubyte),
        ("additional_sense_code_qualifier", ctypes.c_ubyte),
        ("field_replaceable_unit_code", ctypes.c_ubyte),
        ("sense_key_specific", ctypes.c_ubyte * 3),
    ]


class DescriptorFormatSense(ctypes.Structure):
    """
    The SENSE response may be in of two formats - this one, or
    :class:`FixedFormatSense`. The exact format depends on the value of
    the first byte, `error_code`.
    """

    _fields_ = [
        ("error_code", ctypes.c_ubyte, 7),
        ("valid", ctypes.c_ubyte, 1),
        ("sense_key", ctypes.c_ubyte, 4),
        ("reserved_1", ctypes.c_ubyte, 4),
        ("additional_sense_code", ctypes.c_ubyte),
        ("additional_sense_code_qualifier", ctypes.c_ubyte),
    ]


class IdentifyResponse(ctypes.Structure):
    """
    The response to an SCSI/ATA IDENTIFY command.

    .. note::

        This is a large structure, and has only been partially implemented. The
        full response is 512 bytes.
    """

    # I don't have the willpower to implement this entire structure. If you
    # need a field, add it.
    _fields_ = [
        # ('general_config', ctypes.c_ushort),
        ("reserved_1", ctypes.c_ushort, 1),
        ("retired_3", ctypes.c_ushort, 1),
        ("response_incomplete", ctypes.c_ushort, 1),
        ("retired_2", ctypes.c_ushort, 3),
        ("fixed_device", ctypes.c_ushort, 1),
        ("removable_media", ctypes.c_ushort, 1),
        ("retired_1", ctypes.c_ushort, 7),
        ("device_type", ctypes.c_ushort, 1),
        # We don't use the following 18 bytes.
        ("padding_1", ctypes.c_ubyte * 18),
        ("serial_number", ctypes.c_ubyte * 20),
        # We don't use the following 6 bytes.
        ("padding_2", ctypes.c_ubyte * 6),
        ("firmware_revision", ctypes.c_ubyte * 8),
        ("model_number", ctypes.c_ubyte * 40),
    ]


class SmartDataEntry(ctypes.Structure):
    """
    An entry in the SMART attribute table.

    .. note::

        The specification calls this field vendor specific, but its format is
        very consistent.
    """

    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_ubyte),
        ("flags", ctypes.c_ushort),
        ("current", ctypes.c_ubyte),
        ("worst", ctypes.c_ubyte),
        ("vendor_specific_1", ctypes.c_ubyte * 6),
        ("reserved", ctypes.c_ubyte),
    ]


class SmartDataResponse(ctypes.Structure):
    """
    The result of a SMART READ_DATA command.

    .. note::

        The most interesting field in here is likely `vendor_specific_1`,
        which contains the SMART attribute table that encodes values such as
        the current device temperature.

        Although the specification calls this field vendor specific, its
        format is very consistent. See
        :func:`smartie.smart.parse_smart_read_data()` for an example.
    """

    _fields_ = [
        ("version", ctypes.c_ushort),
        ("attributes", SmartDataEntry * 30),
        ("offline_data_collection_status", ctypes.c_ubyte),
        ("self_test_execution_status_buyte", ctypes.c_ubyte),
        ("vendor_specific_2", ctypes.c_ubyte * 2),
        ("vendor_specific_3", ctypes.c_ubyte),
        ("offline_data_collection_capability", ctypes.c_ubyte),
        ("smart_capability", ctypes.c_ushort),
        ("error_logging_capability", ctypes.c_ubyte),
        ("vendor_specific_4", ctypes.c_ubyte),
        # Recommended time is in minutes.
        ("short_self_test_recommended_time", ctypes.c_ubyte),
        # Recommended time is in minutes.
        ("extended_self_test_recommended_time", ctypes.c_ubyte),
        # Recommended time is in minutes.
        ("conveyance_self_test_recommended_time", ctypes.c_ubyte),
        # Recommended time is in minutes.
        ("extended_self_test_recommended_time_wide", ctypes.c_short),
        ("reserved_1", ctypes.c_ubyte * 8),
        ("vendor_specific_2", ctypes.c_ubyte * 124),
        ("data_checksum_structure", ctypes.c_ubyte),
    ]


class SmartThresholdEntry(ctypes.Structure):
    """
    A single entry in the SMART READ_THRESHOLDS response.
    """

    _fields_ = [
        ("attribute_id", ctypes.c_ubyte),
        ("value", ctypes.c_ubyte),
        ("reserved_1", ctypes.c_ubyte * 10),
    ]


class SmartThresholdResponse(ctypes.Structure):
    """
    The result of a SMART READ_THRESHOLDS command.

    .. note::
        The most interesting field in here is likely `vendor_specific_1`,
        which contains the SMART threshold table that encodes values such as
        the temperature at which the device will start throttling.
    """

    _fields_ = [
        ("revision_number", ctypes.c_ushort),
        ("entries", SmartThresholdEntry * 30),
        ("reserved_1", ctypes.c_ubyte * 149),
        ("checksum", ctypes.c_ubyte),
    ]
