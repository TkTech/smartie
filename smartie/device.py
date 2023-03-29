"""
High-level abstractions for enumerating devices and getting basic device
information.
"""
import itertools
import ctypes
import platform
from pathlib import Path
from typing import Iterable, Union


class Device:
    path: str
    fd: int | None

    def __new__(cls, path, *args, **kwargs):
        # This muckery replaces Device with a platform-specific variant
        # whenever Device is used. It's the same trick used by Python's
        # built-in pathlib.Path().
        system = platform.system()
        if system == 'Windows':
            from smartie.scsi.windows import WindowsSCSIDevice
            return WindowsSCSIDevice(*args, **kwargs)
        elif system == 'Linux':
            if 'nvme' in str(path):
                from smartie.nvme.linux import LinuxNVMEDevice
                return LinuxNVMEDevice(path, *args, **kwargs)

            from smartie.scsi.linux import LinuxSCSIDevice
            return LinuxSCSIDevice(path, *args, **kwargs)
        else:
            raise NotImplementedError(
                'Device not implemented for this platform.'
            )

    def __init__(self, path: Union[Path, str]):
        """
        A Device represents a high-level abstraction over a system block
        device.

        :param path: The filesystem path to the device (such as /dev/sda).
        """
        self.path = str(path)
        self.fd = None

    @property
    def model(self) -> str | None:
        """
        Returns the model name of the device.
        """
        return None

    @property
    def serial(self) -> str | None:
        """
        Returns the serial number of the device.
        """
        return None

    @property
    def temperature(self) -> int | None:
        """
        Returns the temperature of the device in degrees Celsius.
        """
        return None

    @property
    def smart_table(self):
        return {}

    def __enter__(self):
        raise NotImplementedError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError()


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
            # This whitelist is guaranteed to be the cause of a headache or
            # two, but I can't currently find a portable way of getting the
            # device "type". We don't want to get encrypted volumes or memory
            # disks, for example.
            if not child.name.startswith(('sd', 'nvme')):
                continue

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
    elif system == 'Darwin':
        from smartie._osx import iokit, cf, kCFBooleanTrue

        io_iterator = ctypes.c_void_p()

        query = iokit.IOServiceMatching(b'IOBlockStorageDevice')
        cf.CFDictionaryAddValue(
            query,
            cf.CFStringCreateWithCString(
                None,
                b'SMART Capable',
                0
            ),
            kCFBooleanTrue
        )

        result = iokit.IOServiceGetMatchingServices(
            0,  # kIOMasterPortDefault
            query,
            ctypes.byref(io_iterator)
        )

        if result != 0:
            raise OSError(ctypes.get_errno())

        while iokit.IOIteratorIsValid(io_iterator):
            io_device = iokit.IOIteratorNext(io_iterator)
            if not io_device:
                break

            name = ctypes.create_string_buffer(512)

            iokit.IORegistryEntryGetPath(
                io_device,
                b'IOService',
                name
            )

            yield Device(name.value)
    else:
        raise NotImplementedError('platform not supported')
