import ctypes
import itertools


def swap_bytes(src):
    # Weirdly, all the strings in the IDENTIFY response are byte swapped.
    src = bytearray(src)

    for i in range(0, len(src) - 1, 2):
        src[i] ^= src[i+1]
        src[i+1] ^= src[i]
        src[i] ^= src[i+1]

    return src


def swap_int(c: int, n: int) -> int:
    return int.from_bytes(
        n.to_bytes(c, byteorder='little'),
        byteorder='big',
        signed=False
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


def embed_bytes(data: bytes, *, line_prefix='    ', max_width=80) -> str:
    """
    Pretty-prints `data` in such a way that it can be embedded cleanly in
    a Python file.

    This exists to embed SCSI commands and responses into tests.

    :param data: The binary data to be formatted.
    :param line_prefix: The prefix to insert before each line.
    :param max_width: The maximum length of each line.
    :return: The formatted result.
    """
    line_length = max_width - len(line_prefix * 2)

    lines = '\n'.join(
        '{prefix}{line}'.format(
            prefix=line_prefix * 2,
            line=', '.join(
                f'0x{byte:02X}' for byte in row
            )
        ) for row in grouper_it(line_length // 6, data)
    )
    return f'{line_prefix}bytearray([\n{lines}\n{line_prefix}])'


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
                f'{name}[{offset}:{offset + bitcount}] = {bytes(value)[:20]!r}'
                f' ({len(value)} bytes)'
            )
        else:
            print(f'{name}[{offset}:{offset + bitcount}] = {value!r}')
        offset += bitcount
