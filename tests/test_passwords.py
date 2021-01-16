from unittest import TestCase, expectedFailure
from functools import partial

from retropass import Password

class TestMetroid(TestCase):
    def setUp(self):
        self.make = partial(Password.make, 'metroid')
        self.default = self.make()

    def test_password_roundtrip(self):
        passwords = ['000000 000000 000000 000000',
                     '0G0000 000000 400000 00000H',
                     'GGW01G 000020 VsG000 00002n',
                     'ENGAGE RIDLEY MOTHER FUCKER',]
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

    def test_known_password_3(self):
        pw = self.make('ENGAGE RIDLEY MOTHER FUCKER')
        self.assertEqual(pw.ridley_dead, 1)
        self.assertEqual(pw.missiles, 82)

    def test_data_length(self):
        self.assertEqual(len(self.default.data), 128)

    def test_pw_length(self):
        self.assertEqual(len(str(self.default)), 24+3)  # +3 for the spaces

class TestSolarJetman(TestCase):
    def setUp(self):
        self.make = partial(Password.make, 'sj')
        self.default = self.make()

    def test_password_roundtrip(self):
        passwords = ['ZQBQQQQQHGTQ',
                     'ZQBQQQQQNMTQ',
                     'ZQBPQQQQTRTQ']
        for text in passwords:
            pw = self.make(text)
            self.assertEqual(text, str(pw))

    def test_known_passwords(self):
        pw = self.make()
        self.assertEqual(str(pw), "BBBBBBBBBBBB")
        pw.level = 6
        self.assertEqual(str(pw), "BBDDBBBBKKBB")
        pw.score = 123456
        self.assertEqual(str(pw), "BMDPKLHGKMBD")
        pw.lives = 3
        self.assertEqual(str(pw), "HMDNKLHGKMBD")
        pw.shields = 1
        self.assertEqual(str(pw), "HMDNKLHGKPGD")
        pw.map = 1
        self.assertEqual(str(pw), "HMDNKLHGMMGD")
        pw.thrusters = 1
        self.assertEqual(str(pw), "HMDNKLHGMLHD")


class TestKidIcarus(TestCase):
    """ By level:
    000000 000000 E30000 0000Yx: 1-1
    000000 000000 m20000 00002q: 1-1
    0000eu 60j700 uG0004 1000J0: 1-4
    0000ys T0J300 m2001C H000aS: 2-1
    00008C i04400 mIG01D I0005F: 2-4
    0000mu w0K200 O3G00H I100s5: 3-1
    0000y0 11X200 u0G00H I100t0: 3-4
    00008p 414100 O3G00H I500eB: 4-1


    """
    def setUp(self):
        self.make = partial(Password.make, 'ki')
        self.default = self.make()

    def test_password_roundtrip(self):
        passwords = ['000000 000000 000000 000000',
                     '000000 000000 000000 0004G0',
                     '000000 000000 E30000 0000Yx']
        for text in passwords:
            pw = self.make(text)
            self.assertEqual(text, str(pw))

    def test_known_passwords(self):
        text = '000000 000000 E30000 0000Yx'
        pw = self.make(text)
        self.assertEqual(text, str(pw))

    def test_known_password_levels(self):
        passwords = {
            "000000 000000 E30000 0000Yx": "1-1",
            "000000 000000 m20000 00002q": "1-1",
            "000000 000000 O10000 0004IU": "1-2",
            "0000aC 10v000 O50000 0004Yw": "1-2",
            "6eW3!! !!!!00 F38W!H C0042N": "1-2",
            "0000eu 60j700 uG0004 1000J0": "1-4",
            "0000ys T0J300 m2001C H000aS": "2-1",
            "C0G00Q G0v500 kO0008 I004af": "2-2",
            "C0W0C? K0e300 ET0008 I0084Z": "2-3",
            "00008C i04400 mIG01D I0005F": "2-4",
            "0000mu w0K200 O3G00H I100s5": "3-1",
            "CeW0qB d0j400 O3000C J104s7": "3-2",
            "EeW1yw h08300 u2000C J1086j": "3-3",
            "0000y0 11X200 u0G00H I100t0": "3-4",
            "00008p 414100 O3G00H I500eB": "4-1",
            }
        from bitarray.util import int2ba
        for text, level in passwords.items():
            pw = self.make(text)
            self.assertEqual(pw.level, level)
            self.assertEqual(str(pw), text)


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


class TestMM3(TestCase):
    def setUp(self):
        self.make = partial(Password.make, 'mm3')
        self.default = self.make()

    def test_load_known_password_1(self):
        # Starting state. No tanks, no bosses defeated
        text = 'C5'
        pw = self.make(text)
        self.assertEqual(pw.tanks, 0)
        self.assertFalse(any(pw.defeated.values()))
        self.assertEqual(text, str(pw))

    def test_load_known_password_2(self):
        text = "B:A1 B:A3 B:B2 B:B5 B:D3 B:F4 A6 E1"
        pw = self.make(text)
        print(pw.defeated)
        self.assertEqual(pw.tanks, 9)
        self.assertTrue(all(pw.defeated.values()))
        self.assertEqual(text, str(pw))

    def test_load_mixed_password(self):
        text = 'B:A3 R:F4 C1 F5'
        pw = self.make(text)
        self.assertEqual(pw.tanks, 5)
        self.assertTrue(pw.defeated['topman'])
        self.assertTrue(pw.defeated['snakeman'])
        self.assertTrue(pw.defeated['sparkman'])
        self.assertTrue(pw.defeated['magnetman'])
        self.assertEqual(str(pw), text)

    def test_create_password(self):
        pw = self.make()
        pw.defeated['topman'] = True
        pw.defeated['snakeman'] = True
        pw.defeated['sparkman'] = True
        pw.defeated['magnetman'] = True
        pw.tanks = 5
        self.assertEqual(str(pw), 'B:A3 R:F4 C1 F5')
