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