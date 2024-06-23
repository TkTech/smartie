Low-level API
=============

While verbose, the low-level API can be used to send any arbitrary command to
devices. SMARTie provides pre-defined enums and structures for many common
commands, but you can also send any command you like by defining your own
``ctypes.Structure``.

.. warning::

  The low-level API can be dangerous - send the wrong command and you could
  permanently wipe or even physically damage your device. Do not use this
  API unless you are absolutely sure of what you are doing. No warranty is
  provided for any damage caused by using this API.

If you don't know what kind of device you have, it may be dangerous to
send arbitrary commands. You can simply use ``isinstance`` to determine the
type of device you have:

.. code-block:: python

  from smartie.device import get_device
  from smartie.scsi import SCSIDevice
  from smartie.nvme import NVMeDevice

  with get_device('\\\\.\\PhysicalDrive0') as device:
      if isinstance(device, SCSIDevice):
          print('SCSI device')
      elif isinstance(device, NVMeDevice):
          print('NVMe device')
      else:
          print('Unknown device type')


SCSI
----

To send an SCSI INQUIRY command to a device:

.. code-block:: python

  import ctypes

  from smartie.scsi import structures
  from smartie.device import get_device

  with get_device('\\\\.\\PhysicalDrive0') as device:
      # The structure that will be populated with the response.
      inquiry = structures.InquiryResponse()

      response = device.issue_command(
          # The direction of the data transfer.
          structures.Direction.FROM,
          # The command to send.
          structures.InquiryCommand(
              operation_code=structures.OperationCode.INQUIRY,
              allocation_length=ctypes.sizeof(inquiry)
          ),
          inquiry
      )

      if response:
        print(inquiry.product_identification)


The ``response`` object we get back from our ``issue_command`` is an
:class:`smartie.scsi.SCSIResponse` object that contains some common
cross-platform fields as well as the raw platform-specific header
that was sent to the device. This can be useful for debugging or
for extracting additional information from the response.

NVMe
----

To send an NVMe IDENTIFY command to a device:

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
