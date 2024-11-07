SMARTie
=======

SMARTie is a pure-python, 0-dependency library for getting basic disk
information such as model, serial number, disk health, temperature,
and SMART data. It supports both SCSI/ATA and NVMe devices.

.. image:: https://img.shields.io/pypi/v/smartie.svg
    :target: https://pypi.org/project/smartie/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/smartie.svg
    :target: https://pypi.org/project/smartie/
    :alt: PyPI supported Python versions

.. image:: https://img.shields.io/pypi/l/smartie.svg
    :target: https://pypi.org/project/smartie/
    :alt: PyPI license


Installation
------------

SMARTie can be installed from PyPI using pip:

.. code-block:: bash

    pip install smartie

If you want the CLI, you can install it with:

.. code-block:: bash

    pip install smartie[cli]

Example Usage
-------------

The high-level interface is designed to be simple and easy to use. For example,
to get the model, serial, and temperature of all devices:

.. code-block:: python

    for device in get_all_devices():
        with device:
            print(device.model, device.serial, device.temperature)


The low-level interface is by necessity more complex, but it provides a way to
send raw SCSI/ATA commands to devices. For example, to get the raw SMART data
from a device:

.. code-block:: python

  import ctypes

  from smartie.scsi import structures
  from smartie.device import get_device

  with get_device('\\\\.\\PhysicalDrive0') as device:
      # The structure that will be populated with the response.
      inquiry = structures.InquiryResponse()

      response = device.issue_command(
          structures.Direction.FROM,
          structures.InquiryCommand(
              operation_code=structures.OperationCode.INQUIRY,
              allocation_length=ctypes.sizeof(inquiry)
          ),
          inquiry
      )

      if response:
        print(inquiry.product_identification)


... or to get the raw NVMe Identify data from a device:

.. code-block:: python

  import ctypes

  from smartie.nvme import structures
  from smartie.device import get_device

  with get_device('/dev/nvme0') as device:
      # The structure that will be populated with the response.
      data = structures.NVMeIdentifyResponse()
      device.issue_admin_command(
          structures.NVMeAdminCommand(
              opcode=structures.NVMeAdminCommands.IDENTIFY,
              addr=ctypes.addressof(data),
              data_len=ctypes.sizeof(data),
              cdw10=1
          )
      )
      print(data.model_number)




Supported Platforms
-------------------

.. list-table::
   :header-rows: 1

   * - OS
     - Device Discovery
     - SCSI/ATA Supported
     - NVMe Supported
   * - Linux
     - Yes
     - Yes
     - Yes
   * - Windows
     - Yes
     - Yes
     - In-progress
   * - OS X
     - Yes
     - In-progress
     - N/A


.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Contents:

   guide/discovery
   guide/high_level
   guide/low_level
   guide/cli
   smartie
