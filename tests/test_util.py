from unittest import TestCase
from functools import partial

from bitarray import bitarray

import retropass.util as util
from retropass.util import rotate, chunk

msb = partial(bitarray, endian='big')
lsb = partial(bitarray, endian='little')

class TestRotate(TestCase):
    def test_noop_rotation(self):
        bits = msb('1000')
        self.assertEqual(rotate(bits, 0), bits)

    def test_rotate_right_big(self):
        bits = msb('1000')
        self.assertEqual(rotate(bits, 1), msb('0100'))

    def test_rotate_left_big(self):
        bits = msb('1000')
        self.assertEqual(rotate(bits, -1), msb('0001'))

    def test_rotate_right_little(self):
        bits = lsb('1000')
        self.assertEqual(rotate(bits, 1), lsb('0100'))

    def test_rotate_left_little(self):
        bits = lsb('1000')
        self.assertEqual(rotate(bits, -1), lsb('0001'))

    def test_rotate_wrap(self):
        bits = msb('1000')
        self.assertEqual(rotate(bits, 4), bits)

    def test_rotate_cancellation(self):
        for ba in lsb, msb:
            bits = ba('100100100100100100')
            rotated = rotate(bits, -1)
            rotated = rotate(rotated, 1)
            self.assertEqual(bits, rotated)

class TestChunk(TestCase):
    def test_chunk(self):
        bits = bitarray('100100100100')
        chunks = list(util.chunk(bits, 3))
        self.assertEqual(len(chunks), 4)
        for chunk in chunks:
            self.assertIsInstance(chunk, bitarray)
            self.assertEqual(len(chunk), 3)
    def test_chunk_length(self):
        bits = bitarray('10000000' * 18)
        chunks = list(util.chunk(bits, 6))
        self.assertEqual(len(chunks), 24)
