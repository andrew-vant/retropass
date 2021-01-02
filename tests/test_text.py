from unittest import TestCase
from string import digits, ascii_uppercase, ascii_lowercase

import retropass.text as text

class TestCodecs(TestCase):
    def test_basics(self):
        codepoints = bytes(range(64))
        alpha = digits + ascii_uppercase + ascii_lowercase + '?-'
        self.assertEqual(alpha.encode('metroid'), codepoints)
        self.assertEqual(codepoints.decode('metroid'), alpha)

    def test_roundtrip(self):
        s = 'thisisastring'
        enc = 'metroid'
        self.assertEqual(s, s.encode(enc).decode(enc))
