# SMARTie

**Note:** This library is in beta. _Please_, create a ticket if you run into an issue.

This is a pure-python library for getting basic disk information such as model,
serial number, disk health, temperature, etc...

It provides a high-level abstraction to enumerate devices and retrieve basic
details:

```python
from smartie.device import get_all_devices

for device in get_all_devices():
    print(device.path)
    print(device.model_number)
    print(device.temperature)
```

... as well as a lower-level interface for sending SCSI messages:

```python
from smartie import structures, constants
from smartie.device import Device

device = Device('\\.\PhysicalDrive0')  # or /dev/sda on Linux
with device.io as dio:
    # Send an SCSI INQUIRY command, and get back both the result data and the
    # sense response.
    result, sense = dio.inquiry()

    # ... or send a raw INQUIRY yourself:
    inquiry = structures.InquiryResponse()

    inquiry_command = structures.InquiryCommand(
        operation_code=constants.OperationCode.INQUIRY,
        allocation_length=96
    )

    sense = dio.issue_command(
        constants.Direction.FROM,
        inquiry_command,
        inquiry
    )
```

## Support

| OS      | SCSI/ATA Supported | NVME Supported | Notes                                      |
|---------|--------------------|----------------|--------------------------------------------|
| Linux   | Yes                | In-progress    | SG_IO v3 (Linux 2.6+)                      |
| Windows | Yes                | In-progress    |                                            |
| OS X    | In-progress*       | N/A            | *IDENTITY and SMART-related commands only. |

OS X explicitly denies access to SCSI/ATA pass-through, _except_ for IDENTITY
and some SMART-related commands, so this is all we can support. Work for OS X
is currently in-progress.

## Installation
SMARTie requires Python 3.8 or greater (due to the use of `@cached_property`).

```
pip install smartie
```

## Why?

This library is extracted from [PortableHardwareMonitor][phm]
monitor, where I don't want to force users to install something like
smartmontools just to support showing disk temperature!

This library ended up being great for poking, prodding, testing and debugging
SCSI/ATA with quick iteration, so hopefully it'll be useful to others.

## Contributing

Compatibility contributions are welcome and greatly encouraged, especially
considering the sheer number of variations of devices out there.

Changes that severely impact readability in exchange for a bit of performance
may be rejected or rewritten. I'm hopeful this library will develop as a
learning resource, and readability is a priority.

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

[S.M.A.R.T]: https://en.wikipedia.org/wiki/S.M.A.R.T.
[phm]: https://github.com/TkTech/PortableHardwareMonitor
[issue]: https://github.com/TkTech/smartie/issues/new.