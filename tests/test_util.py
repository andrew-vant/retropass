from unittest import TestCase

import retropass.util as util
from retropass.util import flip_idx_bitorder

class TestFlipping(TestCase):
    def test_flip(self):
        for i in range(100):
            flipped = flip_idx_bitorder(i)
            self.assertEqual(i // 8, flipped // 8)  # In the same byte
            self.assertEqual((i % 8) + (flipped % 8), 7)

    def test_roundtrip(self):
        for i in range(100):
            self.assertEqual(i, flip_idx_bitorder(flip_idx_bitorder(i)))
