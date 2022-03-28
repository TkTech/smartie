"""
This library does not aim to implement the entire specification, just parts of
it that are useful to PortableHardwareMonitor. However, contributions that
expand support to more devices or implement new commands are extremely welcome.

Support:

- Linux kernel versions > 2.6.6 (required for the SG_IO IOCTL)

.. note::

    Sometimes, I regret my choice of limiting native dependencies. Like the day,
    I wrote this file, for example.

.. warning::

    Uninformed usage of this library can result in data loss or even physical
    destruction of devices. Use low-level commands at your own risk, as they
    will not stop you from sending bad or harmful values.

References:
    - From t10.org (unfortunately can't direct link):
        - spc6r06.pdf
        - 04-262r8.pdf
    - https://sg.danny.cz/sg/p/scsi-generic_v3.txt
    - https://wiki.osdev.org/ATAPI
"""
import os
import stat
import ctypes
import platform
from functools import cached_property
from pathlib import Path
from typing import Iterable, Optional, Union, Dict

from smartie import smart
from smartie.constants import (
    OperationCode,
    ATAProtocol,
    ATACommands,
    SGIODirection,
    IOCTL_SG_IO,
    StatusCode, ATASmartFeature
)
from smartie.errors import SenseError
from smartie.structures import (
    Command16,
    SGIOHeader,
    FixedFormatSense,
    DescriptorFormatSense,
    IdentifyResponse,
    InquiryCommand,
    InquiryResponse, SmartDataResponse
)


class DiskIO:
    disk: 'DiskInfo'
    fd: Optional[int]

    def __init__(self, disk: 'DiskInfo'):
        """
        Used for performing low-level disk IO on the given device.

        :param disk: The block device for all IO operations.
        """
        self.disk = disk
        self.fd = None

    def issue_command(self, direction: 'SGIODirection',
                      command: ctypes.Structure,
                      data: Union[ctypes.Array, ctypes.Structure], *,
                      timeout: int = 3000):
        """
        Issues an ATA passthrough command to the disk.

        :param direction: Direction for this command.
        :param command: Command to be sent to the device.
        :param data: Command data to be sent/received to/from the device.
        :param timeout: SG_IO timeout in milliseconds. Setting this to MAX_INT
                        results in no timeout.
        """
        # The Sense response can be in multiple formats, and we won't know
        # what it is until we see the first byte.
        raw_sense = ctypes.create_string_buffer(max(
            ctypes.sizeof(FixedFormatSense),
            ctypes.sizeof(DescriptorFormatSense)
        ))

        sg_io_header = SGIOHeader(
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

        self.sg_io(sg_io_header)

        # I'm not 100% sure the logic here is even remotely correct. Seems to
        # work!
        if sg_io_header.masked_status == StatusCode.CHECK_CONDITION:
            error_code = int.from_bytes(raw_sense[0], byteorder='little') & 0x7F
            if error_code in (0x70, 0x71):
                sense = FixedFormatSense.from_buffer(raw_sense)
                if sense.sense_key not in (0x01, 0x0F):
                    raise SenseError(sense.sense_key, sense=sense)
                return sense
            elif error_code in (0x72, 0x73):
                sense = DescriptorFormatSense.from_buffer(raw_sense)
                if sense.sense_key not in (0x01, 0x0F):
                    raise SenseError(sense.sense_key, sense=sense)
                return sense
            else:
                raise SenseError(0, sense=raw_sense)

    def sg_io(self, sg_io_header: 'SGIOHeader'):
        """
        Sends an SCSI command to the Disk.

        :param sg_io_header: the SGIOHeader to send to the device.
        """
        system = platform.system()
        if system == 'Linux':
            # We use libc instead of the builtin ioctl as the builtin can have
            # issues with 64-bit pointers.
            libc = ctypes.CDLL('libc.so.6', use_errno=True)

            result = libc.ioctl(
                self.fd,
                IOCTL_SG_IO,
                ctypes.byref(sg_io_header)
            )

            if result != 0:
                raise OSError(ctypes.get_errno())
        else:
            raise NotImplementedError('platform not supported')

    def inquiry(self):
        """
        Issues an SCSI INQUIRY command and returns a tuple of (result, sense).
        """
        inquiry = InquiryResponse()

        inquiry_command = InquiryCommand(
            operation_code=OperationCode.INQUIRY,
            allocation_length=96
        )

        sense = self.issue_command(SGIODirection.FROM, inquiry_command, inquiry)
        return inquiry, sense

    def identify(self):
        """
        Issues an ATA IDENTIFY command and returns a tuple of (result, sense).
        """
        identity = ctypes.create_string_buffer(512)

        command16 = Command16(
            operation_code=OperationCode.COMMAND_16,
            protocol=ATAProtocol.PIO_DATA_IN << 1,
            flags=0x2E,
            command=ATACommands.IDENTIFY
        )

        sense = self.issue_command(SGIODirection.FROM, command16, identity)
        return IdentifyResponse.from_buffer(identity), sense

    def smart_data(self):
        """
        Issues an ATA SMART command and returns a tuple of (result, sense).
        """
        smart_result = SmartDataResponse()

        command16 = Command16(
            operation_code=OperationCode.COMMAND_16,
            protocol=ATAProtocol.PIO_DATA_IN << 1,
            command=ATACommands.SMART,
            flags=0x2E,
            features=swap_int(2, ATASmartFeature.SMART_READ_DATA)
        ).set_lba(0xC24F00)

        sense = self.issue_command(SGIODirection.FROM, command16, smart_result)
        return smart_result, sense

    def is_a_block_device(self):
        return stat.S_ISBLK(os.fstat(self.fd).st_mode)

    def __enter__(self):
        self.fd = os.open(self.disk.path, os.O_RDONLY | os.O_NONBLOCK)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        return False


class DiskInfo:
    path: Path

    def __init__(self, path: Path):
        """
        A DiskInfo represents a high-level abstraction over a system block
        device.

        :param path: The filesystem path to the device (such as /dev/sda).
        """
        self.path = path

        # Is there every a time when we _want_ users to be able to reference
        # a non-existent drive?
        if not path.exists():
            raise IOError(f'{path!s} does not exist')

        with self.io as dio:
            st = os.fstat(dio.fd)
            if not stat.S_ISBLK(st.st_mode):
                raise IOError(f'{path!s} is not a block device')

    @property
    def io(self):
        """
        Returns a DiskIO which can be used as a context manager for IO
        operations. Ex:

        >>> disk = DiskInfo(Path('/dev/sr0'))
        >>> with disk.io as dio:
        ...     identify, sense = dio.identify()
        """
        return DiskIO(self)

    @cached_property
    def identity(self) -> IdentifyResponse:
        """
        The raw, unprocessed response of an ATA IDENTIFY command.

        This property will return an empty :class:`IdentifyResponse` if an
        error occurred.
        """
        with self.io as dio:
            try:
                identity_cache, sense = dio.identify()
            except (OSError, SenseError):
                return IdentifyResponse()
            return identity_cache

    @cached_property
    def inquiry(self) -> InquiryResponse:
        """
        The raw, unprocessed response of an SCSI INQUIRY command to this device.

        This property will return an empty :class:`InquiryResponse` if an
        error occurred.
        """
        with self.io as dio:
            try:
                inquiry_cache, sense = dio.inquiry()
            except (OSError, SenseError):
                return InquiryResponse()
            return inquiry_cache

    @property
    def smart_data(self) -> Dict[int, smart.Attribute]:
        with self.io as dio:
            try:
                smart_result, sense = dio.smart_data()
            except (OSError, SenseError):
                return {}

            return {
                attr.id: attr
                for attr in smart.parse_smart_read_data(smart_result)
            }

    @cached_property
    def model_number(self):
        """
        Get the device's model number, if available.
        """
        v = swap_bytes(self.identity.model_number).strip(b' \x00').decode()
        # If we didn't get anything at all back from an ATA IDENTIFY, try an
        # old fashion SCSI INQUIRY.
        if not v:
            v = bytearray(
                self.inquiry.product_identification
            ).strip(b' \x00').decode()
        return v

    @cached_property
    def serial_number(self):
        """
        Get the device's serial number, if available.
        """
        v = swap_bytes(self.identity.serial_number).strip(b' \x00').decode()
        if not v:
            v = bytearray(
                # This vendor-specific field (almost?) always has the serial
                # number in it.
                self.inquiry.vendor_specific_1
            ).strip(b' \x00').decode()
        return v

    @cached_property
    def device_type(self):
        """
        Get the device's type, if available.
        """
        return self.inquiry.peripheral_device_type

    @property
    def temperature(self):
        """
        Returns the device's temperature in celsius, if available.
        :return:
        """
        temp = self.smart_data.get(0xBE)
        if temp is not None:
            return temp.p_value, temp.p_worst_value

        temp = self.smart_data.get(0xC2)
        if temp is not None:
            return temp.p_value, temp.p_worst_value

    def __repr__(self):
        return (
            f'<{self.__class__.__name__}(path={self.path!r}, model_number='
            f'{self.model_number!r}>'
        )


def swap_bytes(src):
    # Weirdly, all the strings in the IDENTIFY response are byte swapped.
    src = bytearray(src)

    for i in range(0, len(src) - 1, 2):
        src[i] ^= src[i+1]
        src[i+1] ^= src[i]
        src[i] ^= src[i+1]

    return src


def swap_int(c: int, n: int) -> int:
    return int.from_bytes(
        n.to_bytes(c, byteorder='little'),
        byteorder='big',
        signed=False
    )


def get_all_disks(*, raise_errors=False) -> Iterable[DiskInfo]:
    """
    Yields all the block devices detected on the host.

    :param raise_errors: If True, errors that occur while looking for disks
                         will be raised. If False (the default), errors will be
                         ignored.
    """
    system = platform.system()
    if system == 'Linux':
        # There's gotta be a better way of doing this, but I haven't found
        # it yet. We could ask udisk via dbus, or look at /dev/disks/*,
        # but the below gimmick works on the latest beta kernels and the
        # oldest linux kernels I could get my hands on.
        p = Path('/sys/block')
        if p.exists and p.is_dir():
            for child in p.iterdir():
                try:
                    yield DiskInfo(Path('/dev') / child.name)
                except IOError as e:
                    if raise_errors:
                        raise e
    else:
        raise NotImplementedError('platform not supported')
