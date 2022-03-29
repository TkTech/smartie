"""
High-level abstractions for enumerating devices and getting basic device
information.
"""
import os.path
import itertools
import os
import ctypes
import platform
from functools import cached_property
from pathlib import Path
from typing import Iterable, Union, Dict

from smartie import smart, device_io
from smartie.constants import DeviceType
from smartie.errors import SenseError
from smartie.structures import (
    IdentifyResponse,
    InquiryResponse
)
from smartie.util import swap_bytes


class Device:
    path: str

    def __init__(self, path: Union[Path, str]):
        """
        A Device represents a high-level abstraction over a system block
        device.

        :param path: The filesystem path to the device (such as /dev/sda).
        """
        self.path = str(path)

        # Is there every a time when we _want_ users to be able to reference
        # a non-existent drive?
        if not os.path.exists(self.path):
            raise IOError(f'{path!s} does not exist')

        with self.io as dio:
            if not dio.is_a_block_device():
                raise IOError(f'{path!s} is not a block device')

    @property
    def io(self):
        """
        Returns a DeviceIO which can be used as a context manager for IO
        operations. Ex:

        >>> disk = Device(Path('/dev/sr0'))
        >>> with disk.io as dio:
        ...     identify, sense = dio.identify()
        """
        return device_io.DeviceIO(self.path)

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
                smart_result, sense = dio.smart_read_data()
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
        return DeviceType(self.inquiry.peripheral_device_type)

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


def get_all_devices(*, raise_errors=False) -> Iterable[Device]:
    """
    Yields all the devices detected on the host.

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
        if not p.exists or not p.is_dir():
            return

        for child in p.iterdir():
            try:
                yield Device(Path('/dev') / child.name)
            except IOError as e:
                if raise_errors:
                    raise e
    elif system == 'Windows':
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)

        devices = ctypes.create_unicode_buffer(65536)
        # QueryDosDevice will return a list of NULL-terminated strings as a
        # binary blob. Each string is the name of a device (usually hundreds
        # on the typical desktop) that we may or may not care about.
        # The function returns the number of bytes it actually wrote to
        # `devices`.
        bytes_written = k32.QueryDosDeviceW(
            None,
            devices,
            ctypes.sizeof(devices)
        )
        if bytes_written == 0:
            raise RuntimeError('')

        i = 0
        while i < bytes_written:
            # Grab all the characters in the path until we get to the NULL
            # (0x00) byte.
            device_path = ''.join(itertools.takewhile(  # noqa
                lambda c: c != '\x00', devices[i:]
            ))
            i += len(device_path) + 1
            # Ignore every device that doesn't look like PhysicalDrive0, CdRom0,
            # PhysicalDrive1, etc...
            if device_path.startswith(('PhysicalDrive', 'CdRom')):
                # PathLib cannot be used here, there's an option CPython ticket
                # for errors resolving device paths. This is unfortunate,
                # it forced us to revert to a string as the base path type.
                yield Device(f'\\\\.\\{device_path}')
    else:
        raise NotImplementedError('platform not supported')
