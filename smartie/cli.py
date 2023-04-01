import click
from rich import box
from rich.console import Console
from rich.table import Table

from smartie.device import get_all_devices, get_device


@click.group()
def cli():
    """
    Command line interface for SMARTie.
    """


@cli.command('enumerate')
def enumerate_command():
    """
    Enumerate all available devices, displaying basic information.
    """
    table = Table(box=box.SIMPLE)
    table.add_column('Path', style='magenta')
    table.add_column('Model', style='green')
    table.add_column('Serial', style='blue')
    table.add_column('Temperature')

    for device in get_all_devices():
        with device:
            table.add_row(
                device.path,
                device.model,
                device.serial,
                f'{device.temperature}'
            )

    console = Console()
    console.print(table)


@cli.command('details')
@click.argument('path')
def details_command(path: str):
    """
    Show detailed information for a specific device.
    """
    details_table = Table(show_header=False, box=box.MINIMAL)
    details_table.add_column('Key', style='magenta')
    details_table.add_column('Value', style='green')

    with get_device(path) as device:
        details_table.add_row(
            'Model Number',
            device.model
        )
        details_table.add_row(
            'Serial Number',
            device.serial
        )
        details_table.add_row(
            'Temperature',
            f'{device.temperature}°C'
        )

        smart_table = Table(
            title='SMART Attributes',
            title_style='magenta',
            box=box.SIMPLE
        )
        smart_table.add_column('ID', style='magenta')
        smart_table.add_column('Name', style='magenta')
        smart_table.add_column(
            'Current',
            style='green',
            justify='right'
        )
        smart_table.add_column(
            'Worst',
            style='red',
            justify='right'
        )
        smart_table.add_column('Unit', style='italic white')

        for entry in device.smart_table.values():
            smart_table.add_row(
                str(entry.id),
                entry.name,
                str(entry.current_value),
                str(entry.worst_value),
                entry.unit.name
            )

        details_table.add_row(
            '',
            smart_table
        )

    console = Console()
    console.print(details_table)
