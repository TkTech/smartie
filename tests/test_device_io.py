import ctypes
from typing import Union, Optional

from pytest_mock import MockerFixture

from smartie import constants
from smartie.device import Device
from smartie.device_io import DeviceIO


VALID_IDENTIFY_RESPONSE = bytes([
    0x40, 0x00, 0xFF, 0x3F, 0x37, 0xC8, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x3F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x33, 0x51, 0x21, 0x5A,
    0x42, 0x4E, 0x4B, 0x30, 0x32, 0x33, 0x33, 0x35, 0x32, 0x38, 0x20, 0x54,
    0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x56, 0x52,
    0x30, 0x54, 0x42, 0x31, 0x51, 0x36, 0x61, 0x53, 0x73, 0x6D, 0x6E, 0x75,
    0x20, 0x67, 0x53, 0x53, 0x20, 0x44, 0x36, 0x38, 0x20, 0x30, 0x56, 0x45,
    0x20, 0x4F, 0x54, 0x31, 0x20, 0x42, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
    0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20
])


class MockedDeviceIO(DeviceIO):
    def __init__(self, *args, return_data: Optional[bytes] = None,
                 return_sense=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._return_data = return_data
        self._return_sense = return_sense

    def issue_command(self, direction: constants.Direction,
                      command: ctypes.Structure,
                      data: Union[ctypes.Array, ctypes.Structure], *,
                      timeout: int = 3000):

        if self._return_data:
            ctypes.memmove(data, self._return_data, len(self._return_data))

        return self._return_sense

    def is_a_block_device(self) -> bool:
        return True

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def test_identify(mocker: MockerFixture):
    """
    Test we're properly parsing the response to an SCSI/ATA IDENTIFY.
    """
    dio = mocker.patch.object(
        Device,
        'io',
        new_callable=mocker.PropertyMock,
        return_value=MockedDeviceIO(
            '/dev/test',
            return_data=VALID_IDENTIFY_RESPONSE
        )
    )

    device = Device('/dev/test')
    assert device.model_number == 'Samsung SSD 860 EVO 1TB'
    assert device.serial_number == 'Q3Z!NB0K325382T'
