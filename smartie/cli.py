import sys
import json
import ctypes

import click
from rich import box
from rich.console import Console, Group, group
from rich.table import Table

from smartie.database import DRIVE_DATABASE, get_matching_drive_entries
from smartie.device import get_all_devices, get_device
from smartie.nvme import NVMeDevice
from smartie.scsi import SCSIDevice
from smartie.structures import c_uint128, embed_bytes
from smartie.util import grouper_it


@group()
def print_structure(structure: ctypes.Structure, *, indent=0):
    """
    Pretty prints a ctypes.Structure.
    """
    offset = 0

    t = Table(show_lines=True)
    t.add_column("Offset", style="white italic", justify="left")
    t.add_column("Name", style="magenta")
    t.add_column("Value")

    for field in structure._fields_:  # noqa
        if len(field) == 3:
            # If the field has a 3rd part, it's a bitfield, with the 3rd part
            # being the bit count.
            name, type_, bitcount = field
        else:
            name, type_ = field
            bitcount = ctypes.sizeof(type_) * 8

        value = getattr(structure, name)

        if isinstance(value, ctypes.Array):
            array_table = Table(show_header=False)
            array_table.add_column("Hex", no_wrap=True, style="green")
            array_table.add_column("ASCII", no_wrap=True, style="white")

            for chunk in grouper_it(20, bytearray(value)):
                chunk = list(chunk)

                array_table.add_row(
                    " ".join(f"{byte:02X}" for byte in chunk),
                    "".join(
                        chr(byte) if 32 <= byte <= 126 else "."
                        for byte in chunk
                    ),
                )

            t.add_row(
                f"[{offset:03}:{offset + bitcount:03}]", name, array_table
            )
        elif isinstance(value, c_uint128):
            t.add_row(
                f"[{offset:03}:{offset + bitcount:03}]",
                name,
                f"0x{int(value):03X}",
            )
        elif isinstance(value, ctypes.Structure):
            t.add_row(
                f"[{offset:03}:{offset + bitcount:03}]",
                name,
                Group(print_structure(value, indent=indent + 2)),
            )
        elif value is None:
            t.add_row(
                f"[{offset:03}:{offset + bitcount:03}]",
                name,
                "None",
            )
        else:
            t.add_row(
                f"[{offset:03}:{offset + bitcount:03}]",
                name,
                f"0x{int(value):03X}",
            )

        offset += bitcount

    yield t


@click.group()
def cli():
    """
    Command line interface for SMARTie.
    """


@cli.command("enumerate")
def enumerate_command():
    """
    Enumerate all available devices, displaying basic information.
    """
    table = Table(box=box.SIMPLE)
    table.add_column("Path", style="magenta")
    table.add_column("Model", style="green")
    table.add_column("Serial", style="blue")
    table.add_column("Temperature")

    for device in get_all_devices():
        with device:
            table.add_row(
                device.path,
                device.model,
                device.serial,
                f"{device.temperature}",
            )

    console = Console()
    console.print(table)


@cli.command("details")
@click.argument("path")
def details_command(path: str):
    """
    Show detailed information for a specific device.
    """

    def blocks_to_gb(blocks: int) -> float:
        return blocks * 1000 * 512 / 1000 / 1000 / 1000

    details_table = Table(show_header=False)
    details_table.add_column("Key", style="magenta")
    details_table.add_column("Value", style="green")

    with get_device(path) as device:
        details_table.add_row("Model Number", device.model)
        details_table.add_row("Serial Number", device.serial)
        details_table.add_row("Temperature", f"{device.temperature}C")

        smart_table = Table(title="SMART Attributes", title_style="magenta")
        if isinstance(device, SCSIDevice):
            smart_table.add_column("ID", style="white")
            smart_table.add_column("Name", style="magenta")
            smart_table.add_column("Current", style="green", justify="right")
            smart_table.add_column("Worst", style="blue", justify="right")
            smart_table.add_column("Threshold", style="yellow", justify="right")
            smart_table.add_column("Unit", style="italic white")

            for entry in device.smart_table.values():
                smart_table.add_row(
                    str(entry.id),
                    entry.name,
                    str(entry.current_value),
                    str(entry.worst_value),
                    str(entry.threshold),
                    entry.unit.name,
                )
        elif isinstance(device, NVMeDevice):
            smart_table.add_column("Name", style="magenta")
            smart_table.add_column("Value", style="green", justify="right")

            smart, _ = device.smart()

            # We only show a selection of attributes, as the full list is
            # not terribly useful.
            smart_table.add_row(
                "Critical Warning",
                print_structure(smart.critical_warning),
            )
            smart_table.add_row(
                "Temperature", f"{smart.temperature - 273.15:.2f}C"
            )
            smart_table.add_row("Available Spare", f"{smart.available_spare}%")
            smart_table.add_row(
                "Available Spare Threshold",
                f"{smart.available_spare_threshold}%",
            )
            smart_table.add_row("Percentage Used", f"{smart.percent_used}%")
            smart_table.add_row(
                "Data Units Read",
                f"{blocks_to_gb(int(smart.data_units_read)):.2f}GB",
            )
            smart_table.add_row(
                "Data Units Written",
                f"{blocks_to_gb(int(smart.data_units_written)):.2f}GB",
            )
            smart_table.add_row(
                "Host Read Commands", f"{smart.host_read_commands}"
            )
            smart_table.add_row(
                "Host Write Commands", f"{smart.host_write_commands}"
            )
            smart_table.add_row(
                "Controller Busy Time", f"{smart.controller_busy_time}"
            )
            smart_table.add_row("Power Cycles", f"{smart.power_cycles}")
            smart_table.add_row("Power On Hours", f"{smart.power_on_hours}")
            smart_table.add_row("Unsafe Shutdowns", f"{smart.unsafe_shutdowns}")
            smart_table.add_row(
                "Media and Data Integrity Errors", f"{smart.media_errors}"
            )
            smart_table.add_row(
                "Error Information Log Entries", f"{smart.num_err_log_entries}"
            )

            temp_table = Table(expand=True)
            temp_table.add_column("Sensor", style="magenta", justify="center")
            temp_table.add_column(
                "Temperature", style="magenta", justify="center"
            )

            for i, sensor in enumerate(smart.temperature_sensors):
                if sensor != 0x00:
                    temp_table.add_row(str(i), f"{int(sensor - 273.15)}C")

            smart_table.add_row("Temperature Sensors", temp_table)

        details_table.add_row("", smart_table)

    console = Console()
    console.print(details_table)


@cli.command("dump")
@click.argument("path")
@click.argument(
    "command", type=click.Choice(["inquiry", "identify", "smart", "thresholds"])
)
@click.option(
    "--display",
    default="pretty",
    type=click.Choice(["pretty", "raw", "bytearray"]),
)
def dump_command(path: str, command: str, display: str = "pretty"):
    """
    Dump raw responses from an NVMe or ATA device.

    This command can pretty-print rich structures, write raw bytes to stdout,
    or write a bytearray ready for embedding in Python to stdout. Control the
    output with the --display option.
    """
    console = Console()

    with get_device(path) as device:
        if isinstance(device, SCSIDevice):
            result = {
                "inquiry": device.inquiry,
                "identify": device.identify,
                "smart": device.smart,
                "thresholds": device.smart_thresholds,
            }.get(command)
            if result is None:
                console.print("Command unknown or unsupported by this device.")
                return

            structure = result()[0]
        elif isinstance(device, NVMeDevice):
            result = {"identify": device.identify, "smart": device.smart}.get(
                command
            )
            if result is None:
                console.print("Command unknown or unsupported by this device.")
                return

            structure = result()[0]
        else:
            raise NotImplementedError("Unknown device type.")

        if display == "pretty":
            console.print(print_structure(structure))
        elif display == "raw":
            sys.stdout.buffer.write(bytes(structure))  # noqa
        elif display == "bytearray":
            print(embed_bytes(bytearray(structure)))  # noqa


@cli.group("db")
def db_group():
    """
    Commands for querying the disk database.
    """


@db_group.command("export")
def db_export_command():
    """
    Export the disk database as JSON to stdout.

    This is useful for embedding the database in other applications.
    """
    print(
        json.dumps(
            [
                {
                    "name": entry.name,
                    "filters": [
                        f if isinstance(f, str) else f.pattern
                        for f in entry.filters
                    ],
                    "smart_attributes": [
                        {
                            "id": attr.id,
                            "name": attr.name,
                            "unit": attr.unit.name,
                        }
                        for attr in entry.smart_attributes.values()
                    ],
                }
                for entry in DRIVE_DATABASE
            ],
            indent=4,
            sort_keys=True,
        )
    )


@db_group.command("matches")
@click.argument("path")
def db_matches_command(path: str):
    """
    Show all matching entries in the disk database for a specific device.
    """
    console = Console()

    t = Table(box=box.SIMPLE)
    t.add_column("Name", style="magenta", vertical="middle")
    t.add_column("Filters", style="green")

    with get_device(path) as device:
        matches = get_matching_drive_entries(device.get_filters())
        for match in matches:
            filter_table = Table(show_header=False)
            filter_table.add_column("Type", style="white")
            filter_table.add_column("Filter", style="green")

            for f in match.filters:
                filter_table.add_row(
                    f.__class__.__name__,
                    f if isinstance(f, str) else f.pattern,  # noqa
                )

            t.add_row(match.name, filter_table)

    console.print(t)


@cli.group("api")
def api_group():
    """
    Commands for interacting with SMARTie from other applications, such as
    shell scripts.
    """


@api_group.command("list")
def api_list_command():
    """
    List all devices in the system.
    """
    results = []
    for device in get_all_devices():
        with device:
            results.append(
                {
                    "path": device.path,
                    "model": device.model,
                    "serial": device.serial,
                    "temperature": device.temperature,
                }
            )

    print(json.dumps(results, indent=4, sort_keys=True))


@api_group.command("get")
@click.argument("path")
def api_get_command(path: str):
    """
    Get detailed information about a specific device.
    """
    result = {}
    with get_device(path) as device:
        result["path"] = device.path
        result["model"] = device.model
        result["serial"] = device.serial
        result["temperature"] = device.temperature

        if isinstance(device, SCSIDevice):
            result["smart"] = {}
            for entry in device.smart_table.values():
                result["smart"][entry.id] = {
                    "id": entry.id,
                    "current": entry.current_value,
                    "worst": entry.worst_value,
                    "threshold": entry.threshold,
                    "unit": entry.unit.name,
                    "flags": entry.flags,
                }
        elif isinstance(device, NVMeDevice):
            result["smart"] = device.smart_table

    print(json.dumps(result, indent=4, sort_keys=True))
