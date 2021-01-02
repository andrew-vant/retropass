from unittest import TestCase

from retropass import Password

class TestMetroid(TestCase):
    def setUp(self):
        self.default = Password.make('metroid')

    def make(self):
        return Password.make('metroid')

    def test_known_passwords(self):
        pw = self.make()
        pw.taken_marumari = True
        pw.has_marumari = True
        self.assertEqual(str(pw), '0G0000 000000 400000 00000H')

    def test_data_length(self):
        self.assertEqual(len(self.default.data), 128)

    def test_pw_length(self):
        self.assertEqual(len(str(self.default)), 24+3)  # +3 for the spaces
