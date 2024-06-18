![SMARTie logo](misc/logo-sm.png)

# SMARTie

This is a pure-python, 0-dependency library for getting basic disk information
such as model, serial number, disk health, temperature, and SMART data. It
supports both SCSI/ATA and NVMe devices.

## Documentation

Read the getting started guide and API documentation at
https://tkte.ch/smartie/.

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

Some RAID/HBA controllers are known to work and others should as well. If
you're using a RAID controller, and it doesn't work, open an [issue][].

| RAID/HBA Adapter   | OS under test| SCSI Supported | ATA Supported |
|--------------------|--------------|----------------|---------------|
| Broadcom RAID 9440 | CentOS 8.4   | Yes            | Yes           |
| Broadcom RAID 9560 | CentOS 8.4   | Yes            | Yes           |
| Broadcom HBA  9500 | CentOS 8.4   | Yes            | Yes           |
| ThinkSystem   930  | CentOS 8.4   | Yes            | Yes           |
| ThinkSystem   940  | CentOS 8.4   | Yes            | Yes           |
| ThinkSystem   4350 | CentOS 8.4   | Yes            | Yes           |
| ThinkSystem   5350 | CentOS 8.4   | Yes            | Yes           |

Only ``INQUIRY``, ``IDENTIFY`` and ``SMART``-related commands are tested, and
the tests use the latest driver from vendor support web. If it does not work in
your environment, open an [issue][]. The compatibility should be same as
[pydiskcmd][]. Find the testing methodology [here][testingpdc].

### ATA, ATAPI, SCSI, NVMe, what?

Acronyms, acronyms everywhere! What does any of this mean?

- [ATA]: Advanced Technology Attachment.
- [ATAPI]: AT Attachment Packet Interface.
- [SCSI]: Small Computer System Interface. 
- [NVMe]: Non-Volatile Memory Express. The standard for connecting "modern" solid-state
  drives to a computer, typically through [PCI-e].
- [SATA]: Serial ATA. 
- [PATA]: Parallel ATA.
- [S.M.A.R.T]: Self-Monitoring, Analysis, and Reporting Technology. A standard for
  hard drives and solid-state drives to report their health and status.

[ATA]: https://en.wikipedia.org/wiki/ATA
[ATAPI]: https://en.wikipedia.org/wiki/ATAPI
[SCSI]: https://en.wikipedia.org/wiki/SCSI
[NVMe]: https://en.wikipedia.org/wiki/NVMe
[PCI-e]: https://en.wikipedia.org/wiki/PCI_Express
[SATA]: https://en.wikipedia.org/wiki/SATA
[PATA]: https://en.wikipedia.org/wiki/Parallel_ATA
[S.M.A.R.T]: https://en.wikipedia.org/wiki/S.M.A.R.T.
[phm]: https://github.com/TkTech/PortableHardwareMonitor
[issue]: https://github.com/TkTech/smartie/issues/new.
[pydiskcmd]: https://github.com/jackeichen/pydiskcmd?tab=readme-ov-file#raidhba-support
[testingpdc]: https://github.com/jackeichen/pydiskcmd/blob/main/raid_support_matrix_with_smartie.txt
