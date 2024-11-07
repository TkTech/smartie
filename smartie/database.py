"""
Drive and manufacturer-specific quirk database.

This module contains a database of drive and manufacturer-specific quirks,
primarily used for vendor-specific SMART data. This is necessary because
SMART is a specification for _communicating_ with a drive, not a specification
of what SMART data actually means.

.. note::

    It may be very tempting to copy data from sources like smartmontools, which
    has a database of drive-specific quirks. However, these databases are often
    licensed under the GPL, which is incompatible with the MIT license used by
    SMARTie. As such, this database is built from vendor spec sheets when
    possible and guesswork when it's not. If you wish to contribute to this
    database, please do so by submitting a pull request on GitHub.

"""

import enum
import re
from dataclasses import field, dataclass
from typing import Dict, List, Optional


class Units(enum.IntEnum):
    """
    Hints for the possible measurement unit of a SMART attribute, primarily
    used for display purposes.
    """

    UNKNOWN = 0
    CELSIUS = 10
    MILLISECONDS = 20
    HOURS = 21
    COUNT = 30


@dataclass
class SMARTAttribute:
    """
    An Attribute represents a single parsed SMART attribute.
    """

    #: A human-readable identifier, if known.
    name: str
    #: The SMART Attribute ID.
    id: int
    #: The SMART Attribute flags.
    flags: int = 0
    #: If known, a hint for the possible measurement unit in `current_value`.
    unit: Units = Units.UNKNOWN
    #: If provided, a callable function which will be used to process
    #: `current_value` and `worst_value`.
    processor: Optional[callable] = None
    #: The current value of the attribute.
    current_value: Optional[int] = None
    #: The worst known value of the attribute.
    worst_value: Optional[int] = None
    #: The maximum acceptable value of the attribute.
    threshold: Optional[int] = None

    @property
    def p_value(self):
        """
        The current value, run through any provided processor.
        """
        if self.processor is not None:
            return self.processor(self.current_value)
        return self.current_value

    @property
    def p_worst_value(self):
        """
        The worst value, run through any provided processor.
        """
        if self.processor is not None:
            return self.processor(self.worst_value)
        return self.worst_value


@dataclass
class DriveEntry:
    """
    Represents a single entry in the drive database.

    This is used to provide non-standard SMART attributes for specific drives,
    and other drive-specific or manufacturer-specific information.
    """

    name: str
    # A list of filters that a drive must match to use this entry.
    filters: List[str] = field(default_factory=lambda: ["*"])
    # A list of smart attributes that are specific to this drive.
    smart_attributes: Dict[int, SMARTAttribute] = field(default_factory=dict)
    # Maintainer notes.
    notes: List[str] = field(default_factory=list)


DRIVE_DATABASE = [
    DriveEntry(
        name="Default",
        filters=["type:ata"],
        smart_attributes={
            0x01: SMARTAttribute("READ_ERROR_RATE", 0x01),
            0x02: SMARTAttribute("THROUGHPUT_PERFORMANCE", 0x02),
            0x03: SMARTAttribute("SPIN_UP_TIME", 0x03, unit=Units.MILLISECONDS),
            0x04: SMARTAttribute("START_STOP_COUNT", 0x04, unit=Units.COUNT),
            0x05: SMARTAttribute(
                "REALLOCATED_SECTORS_COUNT", 0x05, unit=Units.COUNT
            ),
            0x06: SMARTAttribute("READ_CHANNEL_MARGIN", 0x06),
            0x07: SMARTAttribute("SEEK_ERROR_RATE", 0x07),
            0x08: SMARTAttribute("SEEK_TIME_PERFORMANCE", 0x08),
            # This name is a lie, some manufactures may store minutes or seconds
            # instead of hours.
            0x09: SMARTAttribute("POWER_ON_HOURS", 0x09, unit=Units.HOURS),
            0x0A: SMARTAttribute("SPIN_RETRY_COUNT", 0x0A, unit=Units.COUNT),
            0x0B: SMARTAttribute(
                "RECALIBRATION_RETRIES", 0x0B, unit=Units.COUNT
            ),
            0x0C: SMARTAttribute("POWER_CYCLE_COUNT", 0x0C, unit=Units.COUNT),
            0x0D: SMARTAttribute(
                "SOFT_READ_ERROR_RATE", 0x0D, unit=Units.COUNT
            ),
            0x16: SMARTAttribute("CURRENT_HELIUM_LEVEL", 0x16),
            # TODO: See E8
            0xAA: SMARTAttribute("AVAILABLE_RESERVED_SPACE", 0xAA),
            0xAB: SMARTAttribute(
                "SSD_PROGRAM_FAIL_COUNT", 0xAB, unit=Units.COUNT
            ),
            0xAC: SMARTAttribute(
                "SSD_ERASE_FAIL_COUNT", 0xAC, unit=Units.COUNT
            ),
            0xAD: SMARTAttribute(
                "SSD_WEAR_LEVELING_COUNT", 0xAD, unit=Units.COUNT
            ),
            0xAE: SMARTAttribute("POWER_LOSS_COUNT", 0xAE, unit=Units.COUNT),
            # 0xAF: Attribute('POWER_LOSS_PROTECTION_FAILURE', 0xAF),
            0xB0: SMARTAttribute("ERASE_FAIL_COUNT", 0xB0, unit=Units.COUNT),
            0xB1: SMARTAttribute("WEAR_RANGE_DELTA", 0xB1),
            0xB2: SMARTAttribute(
                "USED_RESERVED_BLOCK_COUNT", 0xB2, unit=Units.COUNT
            ),
            0xB3: SMARTAttribute(
                "USED_RESERVED_BLOCK_COUNT_TOTAL", 0xB3, unit=Units.COUNT
            ),
            0xB4: SMARTAttribute(
                "UNUSED_RESERVED_BLOCK_COUNT_TOTAL", 0xB4, unit=Units.COUNT
            ),
            0xB5: SMARTAttribute(
                "PROGRAM_FAIL_COUNT_TOTAL", 0xB5, unit=Units.COUNT
            ),
            0xB6: SMARTAttribute("ERASE_FAIL_COUNT", 0xB6, unit=Units.COUNT),
            0xB7: SMARTAttribute("RUNTIME_BAD_BLOCK", 0xB7, unit=Units.COUNT),
            0xB8: SMARTAttribute("PARITY_ERROR_COUNT", 0xB8, unit=Units.COUNT),
            0xB9: SMARTAttribute("HEAD_STABILITY", 0xB9),
            0xBA: SMARTAttribute("INDUCED_OP_VIBRATION_DETECTION", 0xBA),
            0xBB: SMARTAttribute(
                "REPORTED_UNCORRECTABLE_ERRORS", 0xBB, unit=Units.COUNT
            ),
            0xBC: SMARTAttribute("COMMANDS_TIMED_OUT", 0xBC, unit=Units.COUNT),
            0xBD: SMARTAttribute("HIGH_FLY_WRITES", 0xBD, unit=Units.COUNT),
            0xBE: SMARTAttribute(
                "TEMPERATURE_DIFFERENCE",
                0xBE,
                unit=Units.CELSIUS,
                processor=lambda v: 100 - v,
            ),
            0xBF: SMARTAttribute("GSENSE_ERROR_RATE", 0xBF, unit=Units.COUNT),
            0xC0: SMARTAttribute(
                "UNSAFE_SHUTDOWN_COUNT", 0xC0, unit=Units.COUNT
            ),
            0xC1: SMARTAttribute("LOAD_CYCLE_COUNT", 0xC1, unit=Units.COUNT),
            0xC2: SMARTAttribute(
                "TEMPERATURE_ABSOLUTE", 0xC2, unit=Units.CELSIUS
            ),
            0xC3: SMARTAttribute("HARDWARE_ECC_RECOVERED", 0xC3),
            0xC4: SMARTAttribute(
                "REALLOCATION_EVENT_COUNT", 0xC4, unit=Units.COUNT
            ),
            0xC5: SMARTAttribute(
                "CURRENT_PENDING_SECTOR_COUNT", 0xC5, unit=Units.COUNT
            ),
            0xC6: SMARTAttribute(
                "UNCORRECTABLE_SECTOR_COUNT", 0xC6, unit=Units.COUNT
            ),
            0xC7: SMARTAttribute(
                "ULTRA_DMA_CRC_ERROR_COUNT", 0xC7, unit=Units.COUNT
            ),
            0xC8: SMARTAttribute("WRITE_ERROR_RATE", 0xC8, unit=Units.COUNT),
            0xC9: SMARTAttribute(
                "SOFT_READ_ERROR_RATE", 0xC9, unit=Units.COUNT
            ),
            0xCA: SMARTAttribute("DATA_ADDRESS_MARKS", 0xCA, unit=Units.COUNT),
            0xCB: SMARTAttribute("RUN_OUT_CANCEL", 0xCB, unit=Units.COUNT),
            0xCC: SMARTAttribute("SOFT_ECC_CORRECTION", 0xCC, unit=Units.COUNT),
            0xCD: SMARTAttribute(
                "THERMAL_ASPERITY_RATE", 0xCD, unit=Units.COUNT
            ),
            0xCE: SMARTAttribute("FLYING_HEIGHT", 0xCE),
            0xCF: SMARTAttribute("SPIN_HEIGHT_CURRENT", 0xCF),
            0xD0: SMARTAttribute("SPIN_BUZZ", 0xD0, unit=Units.COUNT),
            0xD1: SMARTAttribute("OFFLINE_SEEK_PERFORMANCE", 0xD1),
            0xD2: SMARTAttribute("VIBRATION_DURING_WRITE", 0xD2),
            0xD3: SMARTAttribute("VIBRATION_DURING_WRITE", 0xD3),
            0xD4: SMARTAttribute("SHOCK_DURING_WRITE", 0xD4),
            0xDC: SMARTAttribute("DISK_SHIFT", 0xDC),
            0xDD: SMARTAttribute("GSENSE_ERROR_RATE", 0xDD, unit=Units.COUNT),
            0xDE: SMARTAttribute("LOADED_HOURS", 0xDE, unit=Units.HOURS),
            0xDF: SMARTAttribute(
                "LOAD_UNLOAD_RETRY_COUNT", 0xDF, unit=Units.COUNT
            ),
            0xE0: SMARTAttribute("LOAD_FRICTION", 0xE0),
            0xE1: SMARTAttribute(
                "LOAD_UNLOAD_CYCLE_COUNT", 0xE1, unit=Units.COUNT
            ),
            0xE2: SMARTAttribute("LOAD_IN_TIME", 0xE2),
            0xE3: SMARTAttribute(
                "TORQUE_AMPLIFICATION_COUNT", 0xE3, unit=Units.COUNT
            ),
            0xE4: SMARTAttribute(
                "POWER_OFF_RETRACT_CYCLE", 0xE4, unit=Units.COUNT
            ),
            0xE6: SMARTAttribute("THRASHING", 0xE6),
            0xE7: SMARTAttribute("LIFE_LEFT", 0xE7),
            0xE8: SMARTAttribute("ENDURANCE_REMAINING", 0xE8),
            0xE9: SMARTAttribute("MEDIA_WEAROUT_INDICATOR", 0xE9),
            # 0xEA
            # 0xEB
            0xF0: SMARTAttribute("HEAD_FLYING_HOURS", 0xF0, unit=Units.HOURS),
            0xF1: SMARTAttribute("TOTAL_LBAS_WRITTEN", 0xF1, unit=Units.COUNT),
            0xF2: SMARTAttribute("TOTAL_LBAS_READ", 0xF2, unit=Units.COUNT),
            0xF3: SMARTAttribute("TOTAL_LBAS_WRITTEN_EX", 0xF3),
            0xF4: SMARTAttribute("TOTAL_LBAS_READ_EX", 0xF4),
            0xF9: SMARTAttribute("NAND_WRITES", 0xF9),
            0xFA: SMARTAttribute(
                "READ_ERROR_RETRY_RATE", 0xFA, unit=Units.COUNT
            ),
            0xFB: SMARTAttribute("MINIMUM_SPARES_REMAINING", 0xFB),
            0xFC: SMARTAttribute("NEWLY_ADDED_BAD_FLASH_BLOCk", 0xFC),
            0xFE: SMARTAttribute("FREE_FALL_EVENTS", 0xFE, unit=Units.COUNT),
        },
        notes=[
            "The default SMART attributes are based off relatively common"
            " attributes across manufacturers. The attributes are not"
            " guaranteed to be accurate for all drives. If you find any"
            " discrepancies, please open an issue on GitHub."
        ],
    ),
    DriveEntry(
        name="Samsung SSDs",
        filters=[
            "type:ata",
            re.compile(r"model:Samsung SSD 8[56]0 EVO [12]TB"),
        ],
        smart_attributes={
            0xEB: SMARTAttribute("POR_RECOVERY_COUNT", 0xEB, unit=Units.COUNT),
        },
        notes=[
            "Tested against Samsung SSD 850 EVO 2TB",
            "Tested against Samsung SSD 860 EVO 1TB",
        ],
    ),
]


def _match(entry: DriveEntry, filters: List[str]) -> bool:
    """
    Check if the given entry matches the given filters.
    """
    for filter_ in entry.filters:
        if isinstance(filter_, re.Pattern):
            if not any(filter_.match(attr) for attr in filters):
                return False
        elif filter_ not in filters:
            return False

    return True


def get_matching_drive_entries(filters: List[str]) -> List[DriveEntry]:
    """
    Get a list of DriveEntry that matches the given filters.
    """
    return [entry for entry in DRIVE_DATABASE if _match(entry, filters)]


def get_drive_entry(filters: List[str]) -> DriveEntry:
    """
    Get a merged DriveEntry that matches all the given filters.
    """
    entry = DriveEntry(name="_merged_")
    entry.filters = filters

    for matching_entry in get_matching_drive_entries(filters):
        entry.smart_attributes.update(matching_entry.smart_attributes)

    return entry
