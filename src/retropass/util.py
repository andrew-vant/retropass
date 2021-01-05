import os
import sys
import csv
import enum
from enum import Enum
from os.path import dirname, realpath


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

class BitList:
    def __init__(self, parent, offsets):
        self.parent = parent
        self.offsets = list(offsets)

    def __getitem__(self, i):
        return self.parent[self.offsets[i]]

    def __setitem__(self, i, v):
        self.parent[self.offsets[i]] = v

def rotate(bits, n):
    """ Rotate a bitarray n bits

    Positive values of N rotate right; negative values rotate left.
    """
    return bits[-n:] + bits[:-n]

def chunk(bits, chunk_size):
    for i in range(0, len(bits), chunk_size):
        yield bits[i:i+chunk_size]
