from unittest import TestCase

import retropass.text as text

class TestCodecs(TestCase):
    def test_roundtrip(self):
        s = 'thisisastring'
        enc = 'metroid'
        self.assertEqual(s, s.encode(enc).decode(enc))
