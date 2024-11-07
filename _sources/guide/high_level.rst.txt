High-level API
==============

Once we've used one of the discovery methods to find a device, we can use the
high-level API to interact with it and get basic details, regardless of the
underlying implementation:


.. code-block:: python

    import smartie.device

    with smartie.device.get_device("/dev/sdc") as device:
        print(device.model)
        print(device.serial)
        print(device.temperature)

        for attribute in device.smart_table.values():
            print(attribute.name, attribute.current_value)
