from unittest import TestCase

from retropass import Password

class TestMetroid(TestCase):
    def setUp(self):
        self.default = Password.make('metroid')

    def make(self):
        return Password.make('metroid')

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
