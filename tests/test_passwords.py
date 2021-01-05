from unittest import TestCase
from functools import partial

from retropass import Password

class TestMetroid(TestCase):
    def setUp(self):
        self.make = partial(Password.make, 'metroid')
        self.default = self.make()

    def test_password_roundtrip(self):
        passwords = ['000000 000000 000000 000000',
                     '0G0000 000000 400000 00000H',
                     'GGW01G 000020 VsG000 00002n']
        for text in passwords:
            pw = self.make(text)
            self.assertEqual(text, str(pw))

    def test_known_password_1(self):
        pw = self.make()
        pw.taken_marumari = True
        pw.has_marumari = True
        self.assertEqual(str(pw), '0G0000 000000 400000 00000H')

    def test_known_password_2(self):
        pw = self.make()
        pw.has_bombs = 1
        pw.has_boots = 1
        pw.has_longbeam = 1
        pw.has_marumari = 1
        pw.has_screw = 1
        pw.has_varia = 1
        pw.has_wave = 1
        pw.missiles = 100
        pw.taken_bombs = 1
        pw.taken_boots = 1
        pw.taken_marumari = 1
        pw.taken_screw = 1
        pw.taken_varia = 1
        pw.unarmored = 1
        print(pw.checksum)
        self.assertEqual(str(pw), 'GGW01G 000020 VsG000 00002n')

    def test_data_length(self):
        self.assertEqual(len(self.default.data), 128)

    def test_pw_length(self):
        self.assertEqual(len(str(self.default)), 24+3)  # +3 for the spaces

class TestMM2(TestCase):
    def setUp(self):
        self.make = partial(Password.make, 'mm2')
        self.default = self.make()

    def test_known_password_1(self):
        # Starting state. No tanks, all bosses alive.
        text = "A1 B5 C3 C4 D2 D5 E1 E2 E4"
        pw = self.make(text)
        self.assertEqual(pw.tanks, 0)
        for boss in pw.bosses:
            self.assertFalse(pw[boss])
        self.assertEqual(text, str(pw))

    def test_known_password_2(self):
        # Four tanks and all bosses dead
        text = "A5 B2 B4 C1 C3 C5 D4 D5 E2"
        pw = self.make(text)
        self.assertEqual(pw.tanks, 4)
        for boss in pw.bosses:
            self.assertTrue(pw[boss])
        self.assertEqual(text, str(pw))
