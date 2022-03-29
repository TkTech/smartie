"""
This file contains the various low-level structure definitions used for sending
and receiving SCSI commands, as well as the structures required for
platform-specific APIs.

Where reasonable, the names of fields have been taken from the specifications
to ease reference searches.
"""
import ctypes


class InquiryCommand(ctypes.Structure):
    """
    An SCSI INQUIRY command.
    """
    _pack_ = 1
    _fields_ = [
        ('operation_code', ctypes.c_ubyte),
        ('lun', ctypes.c_ubyte),
        ('page_code', ctypes.c_ubyte),
        ('reserved_1', ctypes.c_ubyte),
        ('allocation_length', ctypes.c_ubyte),
        ('control', ctypes.c_ubyte)
    ]


class InquiryResponse(ctypes.Structure):
    """
    The response to an SCSI INQUIRY command.
    """
    _pack_ = 1
    _fields_ = [
        ('peripheral_device_type', ctypes.c_ubyte, 4),
        ('peripheral_qualifier', ctypes.c_ubyte, 4),
        ('reserved_1', ctypes.c_ubyte, 4),
        ('hot_pluggable', ctypes.c_ubyte, 2),
        ('lu_cong', ctypes.c_ubyte, 1),
        ('rmb', ctypes.c_ubyte, 1),
        ('version', ctypes.c_ubyte),
        ('response_data_format', ctypes.c_ubyte, 4),
        ('hi_sup', ctypes.c_ubyte, 1),
        ('norm_aca', ctypes.c_ubyte, 1),
        ('reserved_2', ctypes.c_ubyte, 1),
        ('reserved_3', ctypes.c_ubyte, 1),
        ('additional_length', ctypes.c_ubyte),
        ('protect', ctypes.c_ubyte, 1),
        ('reserved_4', ctypes.c_ubyte, 2),
        ('three_pc', ctypes.c_ubyte, 1),
        ('tpgs', ctypes.c_ubyte, 1),
        ('obsolete_1', ctypes.c_ubyte, 1),
        ('sccs', ctypes.c_ubyte, 1),
        ('obsolete_2', ctypes.c_ubyte, 1),
        ('reserved_5', ctypes.c_ubyte, 1),
        ('reserved_6', ctypes.c_ubyte, 1),
        ('obsolete_3', ctypes.c_ubyte, 1),
        ('multi_p', ctypes.c_ubyte, 1),
        ('vs_1', ctypes.c_ubyte, 1),
        ('enc_serv', ctypes.c_ubyte, 1),
        ('obsolete_4', ctypes.c_ubyte, 1),
        ('vs_2', ctypes.c_ubyte, 1),
        ('cmd_que', ctypes.c_ubyte, 1),
        ('reserved_7', ctypes.c_ubyte, 1),
        ('obsolete_5', ctypes.c_ubyte, 1),
        ('obsolete_6', ctypes.c_ubyte, 2),
        ('reserved_8', ctypes.c_ubyte, 1),
        ('obsolete_7', ctypes.c_ubyte, 1),
        ('t10_vendor_identification', ctypes.c_ubyte * 8),
        ('product_identification', ctypes.c_ubyte * 16),
        ('product_revision_level', ctypes.c_ubyte * 4),
        ('vendor_specific_1', ctypes.c_ubyte * 20),
        ('obsolete_8', ctypes.c_ubyte, 4),
        ('reserved_9', ctypes.c_ubyte, 4),
        ('reserved_10', ctypes.c_ubyte),
        ('version_descriptors', ctypes.c_ushort * 16),
        ('reserved_11', ctypes.c_ubyte * 22),
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
        ('operation_code', ctypes.c_ubyte),
        ('protocol', ctypes.c_ubyte),
        ('flags', ctypes.c_ubyte),
        ('features', ctypes.c_ubyte),
        ('reserved_1', ctypes.c_ubyte, 1),
        ('sector_count', ctypes.c_ubyte, 7),
        ('reserved_2', ctypes.c_ubyte, 1),
        ('lba_low', ctypes.c_ubyte, 7),
        ('reserved_3', ctypes.c_ubyte, 1),
        ('lba_mid', ctypes.c_ubyte, 7),
        ('reserved_4', ctypes.c_ubyte, 1),
        ('lba_high', ctypes.c_ubyte, 7),
        ('device', ctypes.c_ubyte),
        ('command', ctypes.c_ubyte),
        ('reserved_5', ctypes.c_ubyte),
        ('control', ctypes.c_ubyte)
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
        ('operation_code', ctypes.c_ubyte),
        ('protocol', ctypes.c_ubyte),
        ('flags', ctypes.c_ubyte),
        ('features', ctypes.c_ushort),
        ('sector_count', ctypes.c_ushort),
        ('lba_high_low', ctypes.c_ubyte),
        ('lba_low', ctypes.c_ubyte),
        ('lba_high_mid', ctypes.c_ubyte),
        ('lba_mid', ctypes.c_ubyte),
        ('lba_high_high', ctypes.c_ubyte),
        ('lba_high', ctypes.c_ubyte),
        ('device', ctypes.c_ubyte),
        ('command', ctypes.c_ubyte),
        ('control', ctypes.c_ubyte)
    ]

    def set_lba(self, lba: int):
        lba = lba.to_bytes(6, byteorder='little')
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
        ('interface_id', ctypes.c_int),
        ('dxfer_direction', ctypes.c_int),
        ('cmd_len', ctypes.c_ubyte),
        ('mx_sb_len', ctypes.c_ubyte),
        ('iovec_count', ctypes.c_ushort),
        ('dxfer_len', ctypes.c_uint),
        ('dxferp', ctypes.c_void_p),
        ('cmdp', ctypes.c_void_p),
        ('sbp', ctypes.c_void_p),
        ('timeout', ctypes.c_uint),
        ('flags', ctypes.c_uint),
        ('pack_id', ctypes.c_int),
        ('usr_ptr', ctypes.c_void_p),
        ('status', ctypes.c_ubyte),
        ('masked_status', ctypes.c_ubyte),
        ('msg_status', ctypes.c_ubyte),
        ('sb_len_wr', ctypes.c_ubyte),
        ('host_status', ctypes.c_ushort),
        ('driver_status', ctypes.c_ushort),
        ('resid', ctypes.c_int),
        ('duration', ctypes.c_uint),
        ('info', ctypes.c_uint)
    ]


class SCSIPassThroughDirect(ctypes.Structure):
    """
    Corresponds to the SCSI_PASS_THROUGH_DIRECT structure in <ntddscsi.h> on
    Windows.
    """
    _fields_ = [
        ('length', ctypes.c_ushort),
        ('scsi_status', ctypes.c_ubyte),
        ('path_id', ctypes.c_ubyte),
        ('target_id', ctypes.c_ubyte),
        ('lun', ctypes.c_ubyte),
        ('cdb_length', ctypes.c_ubyte),
        ('sense_info_length', ctypes.c_ubyte),
        ('data_in', ctypes.c_ubyte),
        ('data_transfer_length', ctypes.c_uint32),
        ('timeout_value', ctypes.c_uint32),
        ('data_buffer', ctypes.c_void_p),
        ('sense_info_offset', ctypes.c_uint32),
        ('cdb', ctypes.c_ubyte * 16)
    ]


class SCSIPassThroughDirectWithBuffer(ctypes.Structure):
    """
    Corresponds to the SCSI_PASS_THROUGH_DIRECT_WITH_BUFFER structure in
    <ntddscsi.h> on Windows.
    """
    _fields_ = [
        ('sptd', SCSIPassThroughDirect),
        ('filler', ctypes.c_uint32),
        ('sense', ctypes.c_ubyte * 32)
    ]


class FixedFormatSense(ctypes.Structure):
    """
    The SENSE response may be in of two formats - this one, or
    :class:`DescriptorFormatSense`. The exact format depends on the value of
    the first byte, `error_code`.
    """

    _fields_ = [
        ('error_code', ctypes.c_ubyte, 7),
        ('valid', ctypes.c_ubyte, 1),
        ('segment_number', ctypes.c_ubyte),
        ('sense_key', ctypes.c_ubyte, 4),
        ('reserved_1', ctypes.c_ubyte, 1),
        ('ili', ctypes.c_ubyte, 1),
        ('eom', ctypes.c_ubyte, 1),
        ('filemark', ctypes.c_ubyte, 1),
        ('information', ctypes.c_uint32),
        ('additional_sense_length', ctypes.c_ubyte),
        ('command_specific_information', ctypes.c_uint32),
        ('additional_sense_code', ctypes.c_ubyte),
        ('additional_sense_code_qualifier', ctypes.c_ubyte),
        ('field_replaceable_unit_code', ctypes.c_ubyte),
        ('sense_key_specific', ctypes.c_ubyte * 3)
    ]


class DescriptorFormatSense(ctypes.Structure):
    """
    The SENSE response may be in of two formats - this one, or
    :class:`FixedFormatSense`. The exact format depends on the value of
    the first byte, `error_code`.
    """
    _fields_ = [
        ('error_code', ctypes.c_ubyte, 7),
        ('valid', ctypes.c_ubyte, 1),
        ('sense_key', ctypes.c_ubyte, 4),
        ('reserved_1', ctypes.c_ubyte, 4),
        ('additional_sense_code', ctypes.c_ubyte),
        ('additional_sense_code_qualifier', ctypes.c_ubyte)
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
        ('reserved_1', ctypes.c_ushort, 1),
        ('retired_3', ctypes.c_ushort, 1),
        ('response_incomplete', ctypes.c_ushort, 1),
        ('retired_2', ctypes.c_ushort, 3),
        ('fixed_device', ctypes.c_ushort, 1),
        ('removable_media', ctypes.c_ushort, 1),
        ('retired_1', ctypes.c_ushort, 7),
        ('device_type', ctypes.c_ushort, 1),
        # We don't use the following 18 bytes.
        ('padding_1', ctypes.c_ubyte * 18),
        ('serial_number', ctypes.c_ubyte * 20),
        # We don't use the following 6 bytes.
        ('padding_2', ctypes.c_ubyte * 6),
        ('firmware_revision', ctypes.c_ubyte * 8),
        ('model_number', ctypes.c_ubyte * 40)
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
        ('vendor_specific_1', ctypes.c_ubyte * 362),
        ('offline_data_collection_status', ctypes.c_ubyte),
        ('self_test_execution_status_buyte', ctypes.c_ubyte),
        ('vendor_specific_2', ctypes.c_ubyte * 2),
        ('vendor_specific_3', ctypes.c_ubyte),
        ('offline_data_collection_capability', ctypes.c_ubyte),
        ('smart_capability', ctypes.c_ushort),
        ('error_logging_capability', ctypes.c_ubyte),
        ('vendor_specific_4', ctypes.c_ubyte),
        # Recommended time is in minutes.
        ('short_self_test_recommended_time', ctypes.c_ubyte),
        # Recommended time is in minutes.
        ('extended_self_test_recommended_time', ctypes.c_ubyte),
        # Recommended time is in minutes.
        ('conveyance_self_test_recommended_time', ctypes.c_ubyte),
        # Recommended time is in minutes.
        ('extended_self_test_recommended_time_wide', ctypes.c_short),
        ('reserved_1', ctypes.c_ubyte * 8),
        ('vendor_specific_2', ctypes.c_ubyte * 124),
        ('data_checksum_structure', ctypes.c_ubyte)
    ]


def pprint_structure(s: ctypes.Structure):
    """
    Debugging utility method to pretty-print a `ctypes.Structure`.
    """
    offset = 0
    bit = 0

    for field in s._fields_:  # noqa
        if len(field) == 3:
            # Found a bitfield.
            name, type_, bitcount = field
        else:
            name, type_ = field
            bitcount = ctypes.sizeof(type_) * 8

        value = getattr(s, name)
        print(f'{name}[{offset}:{offset + bitcount}] = {value!r}')
        offset += bitcount
