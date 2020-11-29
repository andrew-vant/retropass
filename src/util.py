import os
import sys
import csv
import enum
from enum import Enum
from os.path import dirname, realpath
from collections.abc import Sequence

from bitstring import BitArray, BitStream


libroot = dirname(realpath(__file__))
csv.register_dialect(
        'tsv',
        delimiter='\t',
        lineterminator=os.linesep,
        quoting=csv.QUOTE_NONE,
        strict=True,
        )


def readtsv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f, dialect='tsv'))


class bitorder(Enum):
    lsb0 = enum.auto()
    msb0 = enum.auto()


class byteorder(Enum):
    """ An enum for byte order, because I hate inline strings

    str()ing this will get you just the string. This is so it can be used
    directly as the byteorder arg to int.from_bytes, etc.
    """

    little = 'little'
    big = 'big'
    native = sys.byteorder

    def __str__(self):
        return self.value


# Convenience aliases
lsb0 = bitorder.lsb0
msb0 = bitorder.msb0
be = byteorder.big
le = byteorder.little
ne = byteorder.native


class Field:
    def __init__(self, offset, width, _type, group, order, desc, **kwargs):
        if isinstance(offset, str):
            offset = int(offset, 0)
        if isinstance(width, str):
            width = int(width, 0)

        self.offset = offset
        self.width = width
        self.group = group
        self.order = order
        self.desc = desc
        self.type = _type

        if not self.type:
            if self.width == 1:
                self.type = 'bool'
            elif self.width <= 8:
                self.type = 'uint'
            else:
                msg = "Can't detect type for field >8 bits wide"
                raise ValueError(msg)

    def read(self, bs):
        bs = flip_bs_bitorder(bs)
        start = self.offset
        stop = self.offset + self.width
        bits = bs[start:stop]
        sl = flip_slice_bitorder(self.slice)
        bits = Bits(reversed(bs[start:stop]))
        return getattr(bits, self.type)


    @property
    def slice(self):
        start = self.offset
        stop = start + self.width
        return slice(start, stop)


class Password(Sequence):
    _initialized = False

    def __init__(self, content, fields, encoding, bitorder=bitorder.lsb0):
        # Order matters; bs must be initialized last, because converting
        # `content` to bits may require the other values to be set


        self.bs = None
        self.enc = encoding
        self.bitorder = bitorder
        self.fields = fields
        self._initialized = True

        if isinstance(content, str):
            self.bs = BitArray(self.encode(content))
        elif isinstance(content, bytes):
            self.bs = BitArray(content)
        elif isinstance(content, BitArray):
            self.bs = content

    def _normalize_index(self, idx):
        if self.msb0:
            return idx
        elif isinstance(idx, int):
            return flip_bitorder(idx)
        elif isinstance(idx, slice):
            return flip_slice_bitorder(idx)
        else:
            raise TypeError(f"Don't know what to do with a {type(idx)}")

    def __getitem__(self, i):
        i = self._normalize_index(i)
        return self.bs[i]

    def __setitem__(self, i, v):
        i = self._normalize_index(i)
        self.bs[i] = v

    def __getattr__(self, name):
        if name not in self.fields:
            raise AttributeError(f"No such field: {name}")
        return self[self.fields[name].slice].uint

    def __setattr__(self, name, value):
        if not self._initialized:
            super().__setattr__(self, name, value)
        elif name not in self.fields:
            raise AttributeError(f"Attribute not found: {name}")
        else:
            self.set(name, value)

    def set(self, name, value):
        field = self.fields[name]
        start = field.offset
        stop = field.offset + field.width
        self[start:stop] = BitArray(uint=value, length=field.width)

    @property
    def lsb0(self):
        return self.bitorder is bitorder.lsb0

    @property
    def msb0(self):
        return self.bitorder is bitorder.msb0

    def __str__(self):
        return self.encode()


def flip_idx_bitorder(index):
    """ Helper for turning lsb0 indexes to msb0 indexes, or vice-versa """
    start_of_byte = index // 8
    off_within_byte = index % 8
    return start_of_byte + (7 - off_within_byte)


def flip_bs_bitorder(bs):
    """ reverse the bits in each byte of a bitstring, returning a new one """
    parts = [Bits(reversed(bs[i:i+8]))
             for i in range(0, len(bs), 8)]
    return type(bs)().join(parts)

for i in range(100):
    assert i == flip_bitorder(flip_bitorder(i))
    assert flip_bitorder(i) - i == 7


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


