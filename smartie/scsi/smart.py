"""
Higher level utilities for working with S.M.A.R.T.
"""
import enum
from dataclasses import dataclass, replace
from typing import Dict, Optional

from smartie.scsi.structures import (
    SmartDataResponse,
    SmartThresholdResponse
)


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
class Attribute:
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


#: A table of well-known SMART attributes. These will _generally_ be correct,
#: but may vary by vendor and model.
SMART_ATTRIBUTE_TABLE = {
    0x01: Attribute('READ_ERROR_RATE', 0x01),
    0x02: Attribute('THROUGHPUT_PERFORMANCE', 0x02),
    0x03: Attribute('SPIN_UP_TIME', 0x03, unit=Units.MILLISECONDS),
    0x04: Attribute('START_STOP_COUNT', 0x04, unit=Units.COUNT),
    0x05: Attribute('REALLOCATED_SECTORS_COUNT', 0x05, unit=Units.COUNT),
    0x06: Attribute('READ_CHANNEL_MARGIN', 0x06),
    0x07: Attribute('SEEK_ERROR_RATE', 0x07),
    0x08: Attribute('SEEK_TIME_PERFORMANCE', 0x08),
    # This name is a lie, some manufactures may store minutes or seconds
    # instead of hours.
    0x09: Attribute('POWER_ON_HOURS', 0x09, unit=Units.HOURS),
    0x0A: Attribute('SPIN_RETRY_COUNT', 0x0A, unit=Units.COUNT),
    0x0B: Attribute('RECALIBRATION_RETRIES', 0x0B, unit=Units.COUNT),
    0x0C: Attribute('POWER_CYCLE_COUNT', 0x0C, unit=Units.COUNT),
    0x0D: Attribute('SOFT_READ_ERROR_RATE', 0x0D, unit=Units.COUNT),
    0x16: Attribute('CURRENT_HELIUM_LEVEL', 0x16),
    # TODO: See E8
    0xAA: Attribute('AVAILABLE_RESERVED_SPACE', 0xAA),
    0xAB: Attribute('SSD_PROGRAM_FAIL_COUNT', 0xAB, unit=Units.COUNT),
    0xAC: Attribute('SSD_ERASE_FAIL_COUNT', 0xAC, unit=Units.COUNT),
    0xAD: Attribute('SSD_WEAR_LEVELING_COUNT', 0xAD, unit=Units.COUNT),
    0xAE: Attribute('POWER_LOSS_COUNT', 0xAE, unit=Units.COUNT),
    # 0xAF: Attribute('POWER_LOSS_PROTECTION_FAILURE', 0xAF),
    0xB0: Attribute('ERASE_FAIL_COUNT', 0xB0, unit=Units.COUNT),
    0xB1: Attribute('WEAR_RANGE_DELTA', 0xB1),
    0xB2: Attribute('USED_RESERVED_BLOCK_COUNT', 0xB2, unit=Units.COUNT),
    0xB3: Attribute('USED_RESERVED_BLOCK_COUNT_TOTAL', 0xB3, unit=Units.COUNT),
    0xB4: Attribute(
        'UNUSED_RESERVED_BLOCK_COUNT_TOTAL',
        0xB4,
        unit=Units.COUNT
    ),
    0xB5: Attribute('PROGRAM_FAIL_COUNT_TOTAL', 0xB5, unit=Units.COUNT),
    0xB6: Attribute('ERASE_FAIL_COUNT', 0xB6, unit=Units.COUNT),
    0xB7: Attribute('RUNTIME_BAD_BLOCK', 0xB7, unit=Units.COUNT),
    0xB8: Attribute('PARITY_ERROR_COUNT', 0xB8, unit=Units.COUNT),
    0xB9: Attribute('HEAD_STABILITY', 0xB9),
    0xBA: Attribute('INDUCED_OP_VIBRATION_DETECTION', 0xBA),
    0xBB: Attribute('REPORTED_UNCORRECTABLE_ERRORS', 0xBB, unit=Units.COUNT),
    0xBC: Attribute('COMMANDS_TIMED_OUT', 0xBC, unit=Units.COUNT),
    0xBD: Attribute('HIGH_FLY_WRITES', 0xBD, unit=Units.COUNT),
    0xBE: Attribute(
        'TEMPERATURE_DIFFERENCE',
        0xBE,
        unit=Units.CELSIUS,
        processor=lambda v: 100 - v
    ),
    0xBF: Attribute('GSENSE_ERROR_RATE', 0xBF, unit=Units.COUNT),
    0xC0: Attribute('UNSAFE_SHUTDOWN_COUNT', 0xC0, unit=Units.COUNT),
    0xC1: Attribute('LOAD_CYCLE_COUNT', 0xC1, unit=Units.COUNT),
    0xC2: Attribute('TEMPERATURE_ABSOLUTE', 0xC2, unit=Units.CELSIUS),
    0xC3: Attribute('HARDWARE_ECC_RECOVERED', 0xC3),
    0xC4: Attribute('REALLOCATION_EVENT_COUNT', 0xC4, unit=Units.COUNT),
    0xC5: Attribute('CURRENT_PENDING_SECTOR_COUNT', 0xC5, unit=Units.COUNT),
    0xC6: Attribute('UNCORRECTABLE_SECTOR_COUNT', 0xC6, unit=Units.COUNT),
    0xC7: Attribute('ULTRA_DMA_CRC_ERROR_COUNT', 0xC7, unit=Units.COUNT),
    0xC8: Attribute('WRITE_ERROR_RATE', 0xC8, unit=Units.COUNT),
    0xC9: Attribute('SOFT_READ_ERROR_RATE', 0xC9, unit=Units.COUNT),
    0xCA: Attribute('DATA_ADDRESS_MARKS', 0xCA, unit=Units.COUNT),
    0xCB: Attribute('RUN_OUT_CANCEL', 0xCB, unit=Units.COUNT),
    0xCC: Attribute('SOFT_ECC_CORRECTION', 0xCC, unit=Units.COUNT),
    0xCD: Attribute('THERMAL_ASPERITY_RATE', 0xCD, unit=Units.COUNT),
    0xCE: Attribute('FLYING_HEIGHT', 0xCE),
    0xCF: Attribute('SPIN_HEIGHT_CURRENT', 0xCF),
    0xD0: Attribute('SPIN_BUZZ', 0xD0, unit=Units.COUNT),
    0xD1: Attribute('OFFLINE_SEEK_PERFORMANCE', 0xD1),
    0xD2: Attribute('VIBRATION_DURING_WRITE', 0xD2),
    0xD3: Attribute('VIBRATION_DURING_WRITE', 0xD3),
    0xD4: Attribute('SHOCK_DURING_WRITE', 0xD4),
    0xDC: Attribute('DISK_SHIFT', 0xDC),
    0xDD: Attribute('GSENSE_ERROR_RATE', 0xDD, unit=Units.COUNT),
    0xDE: Attribute('LOADED_HOURS', 0xDE, unit=Units.HOURS),
    0xDF: Attribute('LOAD_UNLOAD_RETRY_COUNT', 0xDF, unit=Units.COUNT),
    0xE0: Attribute('LOAD_FRICTION', 0xE0),
    0xE1: Attribute('LOAD_UNLOAD_CYCLE_COUNT', 0xE1, unit=Units.COUNT),
    0xE2: Attribute('LOAD_IN_TIME', 0xE2),
    0xE3: Attribute('TORQUE_AMPLIFICATION_COUNT', 0xE3, unit=Units.COUNT),
    0xE4: Attribute('POWER_OFF_RETRACT_CYCLE', 0xE4, unit=Units.COUNT),
    0xE6: Attribute('THRASHING', 0xE6),
    0xE7: Attribute('LIFE_LEFT', 0xE7),
    0xE8: Attribute('ENDURANCE_REMAINING', 0xE8),
    0xE9: Attribute('MEDIA_WEAROUT_INDICATOR', 0xE9),
    # 0xEA
    # 0xEB
    0xF0: Attribute('HEAD_FLYING_HOURS', 0xF0, unit=Units.HOURS),
    0xF1: Attribute('TOTAL_LBAS_WRITTEN', 0xF1, unit=Units.COUNT),
    0xF2: Attribute('TOTAL_LBAS_READ', 0xF2, unit=Units.COUNT),
    0xF3: Attribute('TOTAL_LBAS_WRITTEN_EX', 0xF3),
    0xF4: Attribute('TOTAL_LBAS_READ_EX', 0xF4),
    0xF9: Attribute('NAND_WRITES', 0xF9),
    0xFA: Attribute('READ_ERROR_RETRY_RATE', 0xFA, unit=Units.COUNT),
    0xFB: Attribute('MINIMUM_SPARES_REMAINING', 0xFB),
    0xFC: Attribute('NEWLY_ADDED_BAD_FLASH_BLOCk', 0xFC),
    0xFE: Attribute('FREE_FALL_EVENTS', 0xFE, unit=Units.COUNT)
}


def parse_smart_read_data(data: SmartDataResponse, *,
                          threshold: Optional[SmartThresholdResponse] = None)\
        -> Dict[int, Attribute]:
    """
    Parses the SMART attributes out of a SMART READ_DATA command, optionally
    with the corresponding SMART READ_THRESHOLDS data.

    Returns a dictionary of attribute IDs to Attribute objects.
    """
    thresholds = {}
    if threshold:
        for entry in threshold.entries:
            if entry.attribute_id == 0x00:
                break
            thresholds[entry.attribute_id] = entry.value

    result = {}
    for entry in data.attributes:
        if entry.id == 0x00:
            break

        result[entry.id] = replace(
            SMART_ATTRIBUTE_TABLE.get(
                entry.id,
                Attribute(
                    'UNKNOWN',
                    id=entry.id,
                    flags=entry.flags,
                    current_value=entry.current,
                    worst_value=entry.worst,
                    threshold=thresholds.get(entry.id)
                )
            ),
            flags=entry.flags,
            current_value=entry.current,
            worst_value=entry.worst,
            threshold=thresholds.get(entry.id)
        )

    return result
