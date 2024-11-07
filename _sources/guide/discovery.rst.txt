Device Discovery
================

Step one is typically to discover the physical devices present on a system.
The :mod:`smartie.device` module provides functions for discovering devices
on the system.

We can get all devices present on the system by using the
:func:`smartie.device.get_all_devices` function. The mechanism for discovering
devices is platform specific, but typically does not require any special
permissions for the calling user:

.. code-block:: python

    import smartie.device

    devices = smartie.device.get_all_devices()

    for device in devices:
        print(device)


For our example system, this would give us:

.. code-block:: python

    LinuxNVMeDevice(path="/dev/nvme0n1")
    LinuxSCSIDevice(path="/dev/sdb")
    LinuxSCSIDevice(path="/dev/sdc")
    LinuxNVMeDevice(path="/dev/nvme1n1")
    LinuxSCSIDevice(path="/dev/sda")


If we know the device we are interested in, we can also get a specific device
by path:

.. code-block:: python

    import smartie.device

    device = smartie.device.get_device("/dev/nvme0n1")


It's typically recommended to always use one of the discovery functions to
obtain a device object, as it will ensure that the device is valid and
will get the correct device type.