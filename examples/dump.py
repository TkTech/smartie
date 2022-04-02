"""
Dumps the raw response from various built-in commands.

.. note::

    This "example" is used to generate data for embedding into tests.
"""
from smartie.device import get_all_devices
from smartie.errors import SenseError
from smartie.util import embed_bytes

if __name__ == '__main__':
    commands = ['inquiry', 'identify']

    for device in get_all_devices():
        try:
            print(device)
            with device.io as dio:
                for command in commands:
                    response, _ = getattr(dio, command)()

                    print(
                        f'    {command} ='
                        f' {embed_bytes(bytearray(response)).lstrip()}'
                    )
        except SenseError as e:
            print('Sense error occurred:')
            print(f'    {e!r}')
            print(
                f'    sense ='
                f' {embed_bytes(bytearray(e.sense)).lstrip()}'
            )
        except OSError:
            continue
