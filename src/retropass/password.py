import logging
from collections import Counter
from collections.abc import Mapping
from abc import abstractmethod
from string import ascii_uppercase

from bitarray import bitarray
from bitarray.util import ba2int, int2ba, ba2hex, zeros

from .util import rotate, chunk, readtsv, libroot


log = logging.getLogger(__name__)


class InvalidPassword(ValueError):
    def __str__(self):
        return "Invalid password: " + super().__str__()


class Field:
    """ Attributes of a password data field """
    def __init__(self, fid, offset, width, _type='uint', mod=0,
                 group='misc', order=0, desc='', **kwargs):
        if isinstance(offset, str):
            offset = int(offset, 0)
        if isinstance(width, str):
            width = int(width, 0)
        if isinstance(mod, str):
            mod = int(mod, 0) if mod else 0
        if isinstance(order, str):
            order = int(order) if order else 0
        if 'type' in kwargs:
            _type = kwargs['type']

        self.fid = fid
        self.offset = offset
        self.width = width
        self.group = group
        self.order = order
        self.desc = desc
        self.type = _type
        self.mod = mod

    @property
    def slice(self):
        """ The slice of the parent bitarray from which to read this field. """
        start = self.offset
        stop = start + self.width
        return slice(start, stop)

    @classmethod
    def gamefields(cls, game):
        path = f'{libroot}/game/{game}.tsv'
        fields = [Field(**record) for record in readtsv(path)]
        ct_fids = Counter(f.fid for f in fields)

        # Automagically append digits to the fids of duplicated fields
        # FIXME: There should be some way to make this explicit in the file
        # format.
        for fid, count in ct_fids.items():
            if count == 1:
                continue
            for i, field in enumerate((f for f in fields if f.fid == fid), 1):
                field.fid += str(i)

        return {f.fid: f for f in fields}


class Password(Mapping):
    _games = {}
    # This must be provided by subclasses
    gid = None      # Game ID
    default = None  # Default password

    def __init_subclass__(cls):
        if not cls.gid:
            raise ValueError(f"{cls} didn't specify game name")
        cls._games[cls.gid] = cls

    @classmethod
    def make(cls, gid, password=None, infile=None):
        pw = cls._games[gid](password)
        if infile:
            pw.load(infile)
        return pw

    @classmethod
    def supported_games(cls):
        return list(cls._games)

    @abstractmethod
    def __init__(self, password=None):
        """ Construct a password

        Subclasses must implement this. Init must accept a single, optional
        argument, `password`. If the password is not provided, or is None, a
        default must be used. The default password should produce the initial
        game state, if possible.
        """
        raise NotImplementedError

    @abstractmethod
    def __str__(self):
        """ Stringify a password

        Subclasses must implement this. It should print the password as it
        would be entered into the game.
        """
        raise NotImplementedError

    def load(self, f):
        for line in f:
            # Skip comments and blank lines
            if line.startswith("#") or not line.strip():
                continue
            k, v = (part.strip() for part in line.split(":"))
            self[k] = int(v, 0)

    def dump(self):
        out = ''
        colw = max(len(k) for k in self) + 2
        for key, val in self.items():
            key = key + ":"
            val = int(val)
            out += f'{key:{colw}}{val}\n'
        return out



class Structure(Mapping):
    fields = {}
    _initialized = False

    def __init__(self):
        # Subclasses should run super().__init__ *after* doing their own
        # initialization
        self.data = zeros(self.ct_bits, 'little')
        self._initialized = True

    @property
    def ct_bits(self):
        return sum(f.width for f in self.fields.values())

    @property
    def hex(self):
        return ba2hex(self.data)

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def __getattr__(self, name):
        if name not in self.fields:
            raise AttributeError(f"No such field: {name}")
        field = self.fields[name]
        return ba2int(self.data[field.slice]) + field.mod

    def __setattr__(self, name, value):
        if not self._initialized:
            object.__setattr__(self, name, value)
        elif name in self.fields:
            field = self.fields[name]
            value = int(value) - field.mod
            length = field.width
            end = self.data.endian()
            self.data[field.slice] = int2ba(value, length=length, endian=end)
        else:
            super().__setattr__(name, value)

    def __getitem__(self, name):
        if name not in self.fields and not hasattr(self, name):
            raise KeyError(f"No such field: {name}")
        return getattr(self, name)

    def __setitem__(self, name, value):
        if name not in self.fields and not hasattr(self, name):
            raise KeyError(f"No such field: {name}")
        setattr(self, name, value)


class MetroidPassword(Structure, Password):
    gid = 'metroid'
    fields = Field.gamefields(gid)

    def __init__(self, password=None):
        if password is None:
            password = '0' * 24
        password = password.strip().replace(' ', '')  # Remove spaces
        if len(password) != 24:
            raise InvalidPassword("wrong length")

        data = bitarray(endian='big')
        for charcode in password.encode(self.gid):
            data += int2ba(charcode, 6, endian='big')

        self.shift = ba2int(data[-16:-8])
        gamestate = rotate(data[:-16], -self.shift)
        chk_given = ba2int(data[-8:])
        chk_data = (sum(gamestate.tobytes()) + self.shift) % 0x100
        if chk_given != chk_data:
            raise InvalidPassword(f"checksum failure, {chk_given} != {chk_data}")
        self.data = bitarray(gamestate, 'little')

        self._initialized = True

    @property
    def checksum(self):
        return (sum(self.data.tobytes()) + self.shift) % 0x100

    @property
    def codepoints(self):
        # The documentation's bit-numbering is lsb0, but slices for the code
        # points are based on msb0. Hence making a new bitarray with the
        # opposite endianness. I *think* the right thing to do here is to
        # re-index the field offsets according to msb0, but I'm not sure. Try
        # it and see what the spec looks like.
        bits = rotate(bitarray(self.data, 'big'), self.shift)
        bits += int2ba(self.shift, 8)
        bits += int2ba(self.checksum, 8)
        assert len(bits) == 144

        for c in chunk(bits, 6):
            yield ba2int(c)

    def __str__(self):
        pw = bytes(self.codepoints).decode(self.gid)
        return ' '.join(chunk(pw, 6))


class KidIcarusPassword(MetroidPassword):
    gid = 'ki'
    fields = Field.gamefields(gid)

    def __init__(self, password=None):
        if password is None:
            password = '0' * 24
        password = password.strip().replace(' ', '')  # Remove spaces
        if len(password) != 24:
            raise InvalidPassword("wrong length")

        data = bitarray(endian='little')
        for charcode in password.encode(self.gid):
            data += int2ba(charcode, 6, endian='little')
        self.data = bitarray(data[:-8], 'little')
        checksum = ba2int(data[-8:])

        if self.checksum != checksum:
            msg = f"checksum failure, {self.checksum} != {checksum} [{password}]"
            raise InvalidPassword(msg)
        self._initialized = True

    @property
    def level(self):
        sub = 4 if self.maze else self.substage
        return f'{self.stage}-{sub}'

    @level.setter
    def level(self, value):
        stage, substage = (int(part) for part in value.split('-'))
        self.stage = stage
        self.substage = 0 if substage == 4 else substage
        self.maze = int(substage == 4)

    @property
    def bits(self):
        return self.data + int2ba(self.checksum, 8, 'little')

    @property
    def checksum(self):
        return sum(self.data.tobytes()) % 0x100

    @property
    def codepoints(self):
        for c in chunk(bitarray(self.bits, 'little'), 6):
            yield ba2int(c)

class SolarJetmanPassword(Structure, Password):
    # this works like hex with a different alphabet
    charset = 'BDGHKLMNPQRTVWXZ'
    defaultpw = 'BBBBBBBBBBBB'
    gid = 'sj'
    fields = Field.gamefields(gid)

    def __init__(self, password=None):
        super().__init__()
        if password is None:
            password = self.defaultpw
        for i, char in enumerate(password):
            start = i * 4
            end = start + 4
            cp = self.charset.index(char)
            self.data[start:end] = int2ba(cp, 4, 'little')
        assert len(self.data) == self.ct_bits

    @property
    def score(self):
        score = 0
        for exp in range(6):
            digit = self[f'score{exp}']
            score += digit * 10 ** exp
        return score

    @score.setter
    def score(self, value):
        for exp in range(6):
            digit = (value // 10 ** exp) % 10
            self[f'score{exp}'] = digit

    @property
    def level(self):
        return (self.levelhigh << 2) + self.levellow + 1

    @level.setter
    def level(self, value):
        value -= 1
        self.levelhigh = value // 4
        self.levellow = value % 4

    def __iter__(self):
        yield 'level'
        yield 'score'
        for fid, field in self.fields.items():
            if field.order >= 0:
                yield fid

    def __len__(self):
        return len(list(self))

    @property
    def codepoints(self):
        cp = [ba2int(ck) for ck in chunk(self.data, 4)]

        # The checksum algorithm is made of horrible...I feel like there should
        # be a cleaner way to represent this.
        chk1 = ((cp[0] ^ cp[1]) + cp[2] ^ cp[4]) + cp[5]
        chk2 = ((cp[6] ^ cp[7]) + cp[8] ^ cp[10]) + cp[11]

        chk2 += int(chk1 >= 16)
        chk1 += chk2 // 16

        cp[3] = chk1 % 16
        cp[9] = chk2 % 16
        return cp

    def __str__(self):
        return ''.join(self.charset[cp] for cp in self.codepoints)



class MM2Boss:
    def __init__(self, name, alive, dead):
        self.name = name
        self.alive = int(alive)
        self.dead = int(dead)


class MM2Password(Password):
    gid = 'mm2'
    bosses = {record['name']: MM2Boss(**record)
              for record in readtsv(f'{libroot}/game/mm2.tsv')}

    def __init__(self, password=None):
        self.tanks = None
        self.defeated = dict()
        for boss in self.bosses:
            self.defeated[boss] = None

        if password:
            self._load_password(password)
        else:
            self._set_defaults()
        assert self.tanks is not None
        assert not any(state is None for state in self.defeated.values())
        self._initialized = True

    def _set_defaults(self):
        self.tanks = 0
        for name in self.bosses:
            self.defeated[name] = False

    def _load_password(self, password):
        codes = sorted(self.cell2int(cell) for cell in password.split(" "))
        if len(codes) != 9:
            raise InvalidPassword("Wrong length")
        if codes[0] > 4:
            raise InvalidPassword("Tank cell missing")

        self.tanks = codes[0]
        codes = [(code - 5 - self.tanks) % 20
                 for code in codes[1:]]
        for boss in self.bosses.values():
            alive = boss.alive in codes
            dead = boss.dead in codes
            if alive and dead:
                raise InvalidPassword(f"{boss.name} is schrodinger's boss")
            elif alive:
                self[boss.name] = False
            elif dead:
                self[boss.name] = True
            else:
                raise InvalidPassword(f"No state cell for {boss.name}")

    @staticmethod
    def cell2int(cell):
        if len(cell) != 2:
            raise ValueError("Cells are letter-number pairs")
        row = cell[0]
        col = cell[1]
        return (ord(row) - ord('A')) * 5 + (int(col)-1)

    @staticmethod
    def int2cell(i):
        return ascii_uppercase[i // 5] + str(i % 5 + 1)


    def __str__(self):
        codepoints = [self.tanks]
        for boss in self.bosses.values():
            base = boss.dead if self[boss.name] else boss.alive
            code = (base + self.tanks) % 20 + 5
            codepoints.append(code)
        return ' '.join(sorted(self.int2cell(cp) for cp in codepoints))

    def __len__(self):
        return len(self.defeated) + 1

    def __iter__(self):
        yield 'tanks'
        yield from self.bosses.keys()

    def __getitem__(self, k):
        if k == 'tanks':
            return self.tanks
        else:
            return self.defeated[k]

    def __setitem__(self, k, v):
        v = int(v)
        if k == 'tanks':
            self.tanks = v
        else:
            self.defeated[k] = v


class MM3BossPair:
    def __init__(self, boss1, boss2, cell1, cell2, **kwargs):
        self.boss1 = boss1
        self.boss2 = boss2
        self.cell1 = cell1
        self.cell2 = cell2

class MM3Password(Password):
    gid = 'mm3'
    bosses = [MM3BossPair(**record) for record
              in readtsv(f'{libroot}/game/mm3.tsv')]

    # FIXME: All constants should be defined in an external file, I'm just not
    # sure where...
    breakcell = 'E1'
    tankcells = {0: 'C5',
                 1: 'E6',
                 2: 'E4',
                 3: 'B4',
                 4: 'A5',
                 5: 'C1',
                 6: 'D2',
                 7: 'C3',
                 8: 'F2',
                 9: 'A6'}

    def __init__(self, password=None):
        self.tanks = 0
        self.defeated = {}
        for pair in self.bosses:
            self.defeated[pair.boss1] = False
            self.defeated[pair.boss2] = False
        self.defeated['breakman'] = False

        if password:
            self._load_password(password)
        self._initialized = True

    def _load_password(self, password):
        cells = set(password.split())

        for ct, cell in self.tankcells.items():
            cellstrings = [cell, f'R:{cell}', f'B:{cell}']
            if any(cell in cells for cell in cellstrings):
                self.tanks = ct

        for pair in self.bosses:
            b2_defeated = [pair.cell2, 'R:{pair.cell2}', 'B:{pair.cell2}']
            if f'B:{pair.cell1}' in cells:
                self.defeated[pair.boss1] = True
                self.defeated[pair.boss2] = True
            elif f'R:{pair.cell1}' in cells:
                self.defeated[pair.boss1] = True
            elif any(cell in cells for cell in b2_defeated):
                self.defeated[pair.boss2] = True

        bc = self.breakcell  # Convenience alias
        self.defeated['breakman'] = any(cell in cells for cell in
                                        [bc, f'R:{bc}', 'B:{bc}'])

        # FIXME: validate that password represents a valid state, i.e. no
        # late-game bosses beat before earlier-game bosses



    def __str__(self):
        blue = []
        red = []
        either = []

        either.append(self.tankcells[self.tanks])

        for pair in self.bosses:
            if self.defeated[pair.boss1] and self.defeated[pair.boss2]:
                blue.append('B:' + pair.cell1)
            elif self.defeated[pair.boss1]:
                red.append('R:' + pair.cell1)
            elif self.defeated[pair.boss2]:
                either.append(pair.cell2)

        if self.defeated['breakman']:
            either.append(self.breakcell)

        cells = sorted(blue) + sorted(red) + sorted(either)
        return ' '.join(cells)

    def __len__(self):
        return len(self.defeated) + 1

    def __eq__(self, other):
        return self.tanks == other.tanks and self.defeated == other.defeated

    def __iter__(self):
        yield 'tanks'
        yield from self.defeated.keys()

    def __getitem__(self, k):
        if k == 'tanks':
            return self.tanks
        else:
            return self.defeated[k]

    def __setitem__(self, k, v):
        v = int(v)
        if k == 'tanks':
            self.tanks = v
        else:
            self.defeated[k] = v
