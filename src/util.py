from os.path import dirname, realpath

from bitstring import BitStream

libroot = dirname(realpath(__file__))

def pack(_bytes, width):
    """ Pack values into a smaller space

    A number of passwords store values in groups of six bits rather than eight.
    This takes the values from a byte sequence and packs them into six bits
    each, returning a new, smaller byte sequence.
    """
    bits = BitStream()
    for byte in _bytes:
        bits.append(f'uint:6={byte}')
    return bits.bytes


def unpack(_bytes, width):
    """ Unpack n-bit-wide values from a byte sequence """
    bits = BitStream(_bytes)
    out = []
    while True:
        bs = bits.read(width)
        if not bs:
            break;
        out.append(bits.read(width).uint)
    return out

class Struct:
    pass
