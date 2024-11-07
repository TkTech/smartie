"""
High-level abstractions for enumerating devices and getting basic device
information.
"""

import abc
import itertools
import ctypes
import platform
import os
from pathlib import Path
from typing import Iterable, List, Optional, Union


class Device(abc.ABC):
    """
    A Device represents a high-level abstraction over a system block
    device.


    .. note::

        Typically, an end user will never instantiate a Device directly, but
        instead use the :meth:`get_device()` function to get a `Device`
        instance for a given path. This function will automatically determine
        the correct subclass to use based on the platform and device type.

    :param path: The filesystem path to the device (such as /dev/sda).
    """

    path: str
    fd: Optional[int]

    def __init__(self, path: Union[Path, str]):
        self.path = str(path)
        self.fd = None

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path!r})"

    @property
    def model(self) -> Optional[str]:
        """
        Returns the model name of the device.
        """
        return None

    @property
    def serial(self) -> Optional[str]:
        """
        Returns the serial number of the device.
        """
        return None

    @property
    def temperature(self) -> Optional[int]:
        """
        Returns the temperature of the device in degrees Celsius.
        """
        return None

    @property
    def smart_table(self):
        """
        Returns the SMART table for the device, if available.
        """
        return {}

    def get_filters(self) -> List[str]:
        """
        Returns a list of filters that should be used when looking up this
        device in the device database.
        """
        return []

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def get_device(path: Union[Path, str]) -> Device:
    """
    Returns a Device instance for the given path. This is a convenience
    function for the Device constructor which tries to automatically
    determine the correct subclass to use.

    .. code-block:: python

        with get_device("/dev/sda") as device:
            print(device.model, device.serial)

    :param path: The filesystem path to the device (such as /dev/sda).
    """
    # Remember, we always need to use delayed imports here as these imports
    # depend on the platform and may import things that aren't available on
    # all platforms.
    system = platform.system()
    if system == "Windows":
        from smartie.scsi.windows import WindowsSCSIDevice

        return WindowsSCSIDevice(path)
    elif system == "Linux":
        from smartie.nvme.linux import LinuxNVMeDevice
        from smartie.scsi.linux import LinuxSCSIDevice

        if "nvme" in str(path):
            return LinuxNVMeDevice(path)
        return LinuxSCSIDevice(path)
    else:
        raise NotImplementedError("Device not implemented for this platform.")


def get_all_devices() -> Iterable[Device]:
    """
    Yields all the devices detected on the host.

    .. code-block:: python

        for device in get_all_devices():
            with device:
                print(device.model, device.serial)
    """
    system = platform.system()
    if system == "Linux":
        # There's gotta be a better way of doing this, but I haven't found
        # it yet. We could ask udisk via dbus, or look at /dev/disks/*,
        # but the below gimmick works on the latest beta kernels and the
        # oldest linux kernels I could get my hands on.
        p = Path("/sys/block")
        if not p.exists or not p.is_dir():
            return

        for child in p.iterdir():
            # This whitelist is guaranteed to be the cause of a headache or
            # two, but I can't currently find a portable way of getting the
            # device "type". We don't want to get encrypted volumes or memory
            # disks, for example.
            if not child.name.startswith(("sd", "nvme")):
                continue

            # In the new kernel, nvme device may has a character device like
            # nvme0c0n1 (/sys/block/nvme0c0n1), but it is not in the directo
            # -ry /dev/.
            device_path = Path("/dev") / child.name
            if os.path.exists(device_path):
                yield get_device(device_path)
    elif system == "Windows":
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)

        devices = ctypes.create_unicode_buffer(65536)
        # QueryDosDevice will return a list of NULL-terminated strings as a
        # binary blob. Each string is the name of a device (usually hundreds
        # on the typical desktop) that we may or may not care about.
        # The function returns the number of bytes it actually wrote to
        # `devices`.
        bytes_written = k32.QueryDosDeviceW(
            None, devices, ctypes.sizeof(devices)
        )
        if bytes_written == 0:
            raise RuntimeError("")

        i = 0
        while i < bytes_written:
            # Grab all the characters in the path until we get to the NULL
            # (0x00) byte.
            device_path = "".join(
                itertools.takewhile(lambda c: c != "\x00", devices[i:])  # noqa
            )
            i += len(device_path) + 1
            # Ignore every device that doesn't look like PhysicalDrive0, CdRom0,
            # PhysicalDrive1, etc...
            if device_path.startswith(("PhysicalDrive", "CdRom")):
                # PathLib cannot be used here, there's an option CPython ticket
                # for errors resolving device paths. This is unfortunate,
                # it forced us to revert to a string as the base path type.
                yield get_device(f"\\\\.\\{device_path}")
    elif system == "Darwin":
        from smartie.platforms.osx import iokit, cf, kCFBooleanTrue

        io_iterator = ctypes.c_void_p()

        query = iokit.IOServiceMatching(b"IOBlockStorageDevice")
        cf.CFDictionaryAddValue(
            query,
            cf.CFStringCreateWithCString(None, b"SMART Capable", 0),
            kCFBooleanTrue,
        )

        result = iokit.IOServiceGetMatchingServices(
            0,
            query,
            ctypes.byref(io_iterator),  # kIOMasterPortDefault
        )

        if result != 0:
            raise OSError(ctypes.get_errno())

        while iokit.IOIteratorIsValid(io_iterator):
            io_device = iokit.IOIteratorNext(io_iterator)
            if not io_device:
                break

            name = ctypes.create_string_buffer(512)

            iokit.IORegistryEntryGetPath(io_device, b"IOService", name)

            yield get_device(name.value)
    else:
        raise NotImplementedError("platform not supported")
