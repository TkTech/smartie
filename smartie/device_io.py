"""
    Low-level interfaces for sending and receiving SCSI command.

    .. warning::

        Uninformed usage of this library can result in data loss or even
        physical destruction of devices. Use low-level commands at your own
        risk, as they will not stop you from sending bad or harmful values.
"""
import os
import stat
import ctypes
import platform
from pathlib import Path
from typing import Optional, Union

from smartie import util, structures, constants
from smartie.errors import SenseError


class DeviceIO:
    path: str
    fd: Optional[int]

    def __new__(cls, *args, **kwargs):
        # This muckery replaces DeviceIO with a platform-specific variant
        # whenever DeviceIO is used. It's the same trick used by Python's
        # built-in pathlib.Path().
        system = platform.system()
        if system == 'Windows':
            return _WinDeviceIO(*args, **kwargs)
        elif system == 'Linux':
            return _LinuxDeviceIO(*args, **kwargs)
        else:
            raise NotImplementedError(
                'DeviceIO not implemented for this platform.'
            )

    def __init__(self, path: Union[str, Path]):
        """
        A DeviceIO object is used for performing low-level device IO on the
        device specified by `path`.

        >>> from smartie.device_io import DeviceIO
        >>> with DeviceIO('/dev/sda') as dio:
        ...     result, sense = dio.inquiry()

        .. note::

            When you create this object, what you actually get back will be
            a platform-specific variant such as :class:`_WinDeviceIO` or
            :class:`_LinuxDeviceIO`.

        :param path: The filesystem path to the device, such as `/dev/sda` or
                     `\\.\\PhysicalDevice0` (note the escaped slashes).
        """
        self.path = str(path)
        self.fd = None

    def issue_command(self, direction: constants.Direction,
                      command: ctypes.Structure,
                      data: Union[ctypes.Array, ctypes.Structure], *,
                      timeout: int = 3000):
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
        inquiry = structures.InquiryResponse()

        inquiry_command = structures.InquiryCommand(
            operation_code=constants.OperationCode.INQUIRY,
            allocation_length=96
        )

        sense = self.issue_command(
            constants.Direction.FROM,
            inquiry_command,
            inquiry
        )

        return inquiry, sense

    def identify(self):
        """
        Issues an ATA IDENTIFY command and returns a tuple of (result, sense).
        """
        identity = ctypes.create_string_buffer(512)

        command16 = structures.Command16(
            operation_code=constants.OperationCode.COMMAND_16,
            protocol=constants.ATAProtocol.PIO_DATA_IN << 1,
            flags=0x2E,
            command=constants.ATACommands.IDENTIFY
        )

        sense = self.issue_command(
            constants.Direction.FROM,
            command16,
            identity
        )

        return structures.IdentifyResponse.from_buffer(identity), sense

    def smart_read_data(self):
        """
        Issues an ATA SMART READ_DATA command and returns a tuple of
        (result, sense).
        """
        smart_result = structures.SmartDataResponse()

        command16 = structures.Command16(
            operation_code=constants.OperationCode.COMMAND_16,
            protocol=constants.ATAProtocol.PIO_DATA_IN << 1,
            command=constants.ATACommands.SMART,
            flags=0x2E,
            features=util.swap_int(2, constants.ATASmartFeature.SMART_READ_DATA)
        ).set_lba(0xC24F00)

        sense = self.issue_command(
            constants.Direction.FROM,
            command16,
            smart_result
        )

        return smart_result, sense

    def is_a_block_device(self) -> bool:
        """
        Returns `True` if the device is really a block device, `False`
        otherwise.
        """
        return stat.S_ISBLK(os.fstat(self.fd).st_mode)

    @classmethod
    def _parse_sense(cls, sense_blob):
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
            sense = structures.FixedFormatSense.from_buffer_copy(sense_blob)
            if sense.sense_key not in (0x00, 0x01, 0x0F):
                raise SenseError(sense.sense_key, sense=sense)
            return sense
        elif error_code in (0x72, 0x73):
            sense = structures.DescriptorFormatSense.from_buffer_copy(
                sense_blob
            )
            if sense.sense_key not in (0x00, 0x01, 0x0F):
                raise SenseError(sense.sense_key, sense=sense)
            return sense
        else:
            raise SenseError(0, sense=sense_blob)

    def __enter__(self):
        raise NotImplementedError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError()


class _LinuxDeviceIO(DeviceIO):
    """
    The backend for DeviceIO on Linux.
    """
    @classmethod
    def _get_libc(cls):
        # Opens the libc.so, which can be quite a slow process, and
        # saves it for future use.
        libc = getattr(cls, '_libc', None)
        if libc is None:
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            cls._libc = libc
        return libc

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __enter__(self):
        self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        return False

    def issue_command(self, direction: constants.Direction,
                      command: ctypes.Structure,
                      data: Union[ctypes.Array, ctypes.Structure], *,
                      timeout: int = 3000):
        # The Sense response can be in multiple formats, and we won't know
        # what it is until we see the first byte.
        raw_sense = ctypes.create_string_buffer(max(
            ctypes.sizeof(structures.FixedFormatSense),
            ctypes.sizeof(structures.DescriptorFormatSense)
        ))

        sg_io_header = structures.SGIOHeader(
            interface_id=83,  # Always 'S'
            dxfer_direction=direction,
            cmd_len=ctypes.sizeof(command),
            cmdp=ctypes.addressof(command),
            dxfer_len=ctypes.sizeof(data),
            dxferp=ctypes.addressof(data),
            mx_sb_len=ctypes.sizeof(raw_sense),
            sbp=ctypes.addressof(raw_sense),
            timeout=timeout
        )

        # We use libc instead of the builtin ioctl as the builtin can have
        # issues with 64-bit pointers.
        result = self._get_libc().ioctl(
            self.fd,
            constants.IOCTL_SG_IO,
            ctypes.byref(sg_io_header)
        )

        if result != 0:
            raise OSError(ctypes.get_errno())

        return self._parse_sense(raw_sense.raw)


class _WinDeviceIO(DeviceIO):
    """
    The backend for DeviceIO on Windows.
    """
    @classmethod
    def _kernel32(cls):
        # Opens the Kernel32.dll, which can be quite a slow process, and
        # saves it for future use.
        k32 = getattr(cls, '_k32', None)
        if k32 is None:
            k32 = ctypes.WinDLL('kernel32', use_last_error=True)
            cls._k32 = k32
        return k32

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __enter__(self):
        # We can't use the normal approach to opening a file on Windows, as
        # various Python APIs can't handle a device opened without specific
        # flags, see (https://bugs.python.org/issue37074)
        self.fd = self._kernel32().CreateFileW(
            self.path,
            0x80000000 | 0x40000000,  # GENERIC_READ | GENERIC_WRITE
            0x00000001,  # FILE_SHARE_READ
            None,
            0x00000003,  # OPEN_EXISTING
            0x00000080,  # FILE_ATTRIBUTE_NORMAL,
            None
        )

        if self.fd == -1:
            raise ctypes.WinError(ctypes.get_last_error())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            self._kernel32().CloseHandle(self.fd)
            self.fd = None
        return False

    def is_a_block_device(self):
        # FIXME: We need an implementation of this for Windows. Haven't yet
        #        found an API that wasn't convoluted.
        return True

    def issue_command(self, direction: constants.Direction,
                      command: ctypes.Structure,
                      data: Union[ctypes.Array, ctypes.Structure], *,
                      timeout: int = 3000):

        # On Windows, the command block is always 16 bytes, but we may be
        # sending a smaller command. We use a temporary mutable bytearray for
        # this.
        cdb = (ctypes.c_ubyte * 16).from_buffer_copy(
            bytearray(command).ljust(16, b'\x00')  # noqa
        )

        header_with_buffer = structures.SCSIPassThroughDirectWithBuffer(
            sptd=structures.SCSIPassThroughDirect(
                length=ctypes.sizeof(structures.SCSIPassThroughDirect),
                data_in={
                    constants.Direction.TO: 0,
                    constants.Direction.FROM: 1
                }.get(direction),
                data_transfer_length=ctypes.sizeof(data),
                data_buffer=ctypes.addressof(data),
                cdb_length=ctypes.sizeof(command),
                cdb=cdb,
                timeout_value=timeout,
                sense_info_length=(
                    structures.SCSIPassThroughDirectWithBuffer.sense.size
                ),
                sense_info_offset=(
                    structures.SCSIPassThroughDirectWithBuffer.sense.offset
                )
            )
        )

        result = self._kernel32().DeviceIoControl(
            self.fd,
            0x4D014,  # IOCTL_SCSI_PASS_THROUGH_DIRECT,
            ctypes.pointer(header_with_buffer),
            ctypes.sizeof(header_with_buffer),
            ctypes.pointer(header_with_buffer),
            ctypes.sizeof(header_with_buffer),
            None,
            None
        )

        self._parse_sense(bytearray(header_with_buffer.sense))

        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())

        return header_with_buffer.sense

