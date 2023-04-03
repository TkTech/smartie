import ctypes
import itertools
from typing import Any, Dict

from smartie.structures import c_uint128


def swap_bytes(src):
    # Weirdly, all the strings in the IDENTIFY response are byte swapped.
    src = bytearray(src)

    for i in range(0, len(src) - 1, 2):
        src[i] ^= src[i + 1]
        src[i + 1] ^= src[i]
        src[i] ^= src[i + 1]

    return src


def swap_int(c: int, n: int) -> int:
    return int.from_bytes(
        n.to_bytes(c, byteorder="little"), byteorder="big", signed=False
    )


def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)


def embed_bytes(data: bytes, *, indent=0, char="    ", max_width=80) -> str:
    """
    Pretty-prints `data` in such a way that it can be embedded cleanly in
    a Python file.

    This exists to embed SCSI commands and responses into tests.

    :param data: The binary data to be formatted.
    :param indent: The number of characters to indent each line.
    :param char: The character to use for indentation.
    :param max_width: The maximum length of each line.
    :return: The formatted result.
    """
    prefix = char * indent
    line_length = max_width - len(prefix)

    lines = "\n".join(
        "{prefix}{line}".format(
            prefix=char * (indent + 1),
            line=", ".join(f"0x{byte:02X}" for byte in row),
        )
        for row in grouper_it(line_length // 6, data)
    )
    return f"{prefix}bytearray([\n{lines}\n{prefix}])"


def pprint_structure(s: ctypes.Structure):
    """
    Debugging utility method to pretty-print a `ctypes.Structure`.
    """
    offset = 0
    bit = 0

    for field in s._fields_:  # noqa
        if len(field) == 3:
            # Found a bitfield.
            name, type_, bitcount = field
        else:
            name, type_ = field
            bitcount = ctypes.sizeof(type_) * 8

        value = getattr(s, name)
        if isinstance(value, ctypes.Array):
            print(
                f"{name}[{offset}:{offset + bitcount}] = {bytes(value)[:15]!r}"
                f" ({len(value)} bytes)"
            )
            print(embed_bytes(bytes(value)))
        else:
            print(f"{name}[{offset}:{offset + bitcount}] = {value!r}")
        offset += bitcount


def structure_to_dict(s: ctypes.Structure) -> Dict[str, Any]:
    """
    Converts a `ctypes.Structure` into a dictionary.
    """
    result = {}

    for field in s._fields_:  # noqa
        name = field[0]
        value = getattr(s, name)

        if isinstance(value, ctypes.Array):
            result[name] = [v for v in value]
        elif isinstance(value, c_uint128):
            result[name] = int(value)
        elif isinstance(value, ctypes.Structure):
            result[name] = structure_to_dict(value)
        else:
            result[name] = value

    return result
