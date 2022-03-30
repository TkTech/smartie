"""
This quick example will print basic SMART attributes for all found devices.
"""
from smartie.device import get_all_devices

if __name__ == '__main__':
    for device in get_all_devices():
        print('*' * 80)
        print(f'- {device.path!s} ({device.model_number})')
        for attribute in device.smart_data.values():
            print(f'  - {attribute}')