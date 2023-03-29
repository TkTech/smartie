import abc

from smartie.device import Device


class NVMEDevice(Device, abc.ABC):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
