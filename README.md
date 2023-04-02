![SMARTie logo](misc/logo-sm.png)

# SMARTie

This is a pure-python, 0-dependency library for getting basic disk information such as model,
serial number, disk health, temperature, and SMART data. It supports both SCSI/ATA and NVMe devices.

It provides a high-level abstraction to enumerate devices and retrieve basic
details:

```python
from smartie.device import get_all_devices

for device in get_all_devices():
    print(device.path)
    print(device.model)
    print(device.serial)
    print(device.temperature)

    for attribute in device.smart_table:
        print(attribute.name, attribute.value)
```

... as well as a lower-level interface for sending raw messages to devices, such as an SCSI INQUIRY:

```python
import smartie.scsi.structures
from smartie.scsi import constants, structures
from smartie.device import get_device

with get_device('\\.\PhysicalDrive0') as device:
  # The structure that will be populated with the response.
  inquiry = structures.InquiryResponse()

  # The command we're going to send to the device.
  inquiry_command = structures.InquiryCommand(
    operation_code=smartie.scsi.structures.OperationCode.INQUIRY,
    allocation_length=96
  )

  # And finally issue the command. The response will be populated into the
  # `inquiry` structure, and the `sense` structure will contain any error
  # information.
  sense = device.issue_command(
    smartie.scsi.structures.Direction.FROM,
    inquiry_command,
    inquiry
  )
```

## Support

| OS      | SCSI/ATA Supported | NVME Supported | Notes                                      |
|---------|--------------------|----------------|--------------------------------------------|
| Linux   | Yes                | Yes            | SG_IO v3 (Linux 2.6+)                      |
| Windows | Yes                | In-progress    |                                            |
| OS X    | In-progress*       | N/A            | *IDENTITY and SMART-related commands only. |

OS X explicitly denies access to SCSI/ATA pass-through, _except_ for IDENTITY
and some SMART-related commands, so this is all we can support. Work for OS X
is currently in-progress.

## Installation
SMARTie currently requires Python 3.8 or greater.

```
pip install smartie
```

If you want the command line tools, you'll also want to do:

```
pip install smartie[cli]
```

## FAQ

### This library isn't returning any of my drives?

The APIs this library uses to communicate with devices typically require
root (on Linux) or administrator (on Windows) access to work.

### My drive doesn't work with this library?

Support for drives that don't follow modern standards is still a work in
progress. Open an [issue][].

### Library Y does X, can I copy that code?

**It depends.** This library is available under the MIT license and is a fun side
project. I want anyone to be able to use it. Many existing projects are GPL or
LGPL, so you need to avoid them when contributing to this project. Instead:

- Use the specifications or vendor documentation whenever possible.
- Use the SG_IO documentation by Danny (https://sg.danny.cz/sg/).
- Use the _conversations_ in mailing lists and bug trackers, while avoiding the
  code.

### Does this library support RAID controllers?

Sometimes. It hasn't been thoroughly tested with RAID controllers, as the target audience
for the main program that uses this library is consumer desktops. Patches happily
accepted if you have one to test with!

[S.M.A.R.T]: https://en.wikipedia.org/wiki/S.M.A.R.T.
[phm]: https://github.com/TkTech/PortableHardwareMonitor
[issue]: https://github.com/TkTech/smartie/issues/new.