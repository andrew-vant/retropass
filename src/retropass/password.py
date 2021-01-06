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
        elif name not in self.fields:
            raise AttributeError(f"No such field: {name}")
        else:
            field = self.fields[name]
            value = int(value) - field.mod
            length = field.width
            end = self.data.endian()
            self.data[field.slice] = int2ba(value, length=length, endian=end)

    def __getitem__(self, name):
        if name not in self.fields:
            raise KeyError(f"No such field: {name}")
        return getattr(self, name)

    def __setitem__(self, name, value):
        if name not in self.fields:
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
        self.data = bitarray(data[:-16], 'little')
        self.shift = ba2int(data[-16:-8])
        checksum = ba2int(data[-8:])

        if self.checksum != checksum:
            raise InvalidPassword("checksum failure, ")

        self._initialized = True

    @property
    def bits(self):
        bits = rotate(self.data, self.shift)
        bits += int2ba(self.shift, 8, 'little')
        bits += int2ba(self.checksum, 8, 'little')
        return bits

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

        for c in chunk(bitarray(self.bits, 'big'), 6):
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

class SolarJetmanPassword(Password):
    # this works like hex with a different alphabet
    charset = 'BDGHKLMNPQRTVWXZ'
    defaultpw = 'BBBBBBBBBBBB'
    gid = 'sj'

    def __init__(self, password=None):
        if password is None:
            password = self.defaultpw
        values = [self.charset.index(c) for c in password]

        self.level = 0
        self.score = 0
        self.ship = 0
        self.lives = 0
        self.map = 0
        self.supermap = 0
        self.thrusters = 0
        self.shields = 0

    def __iter__(self):
        for key in [
                'level',
                'score',
                'ship',
                'lives',
                'map',
                'supermap',
                'thrusters',
                'shields',
                ]:
            yield key

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        if k in self:
            setattr(self, k, int(v))
        else:
            raise KeyError

    def __len__(self):
        return 8

    @property
    def codepoints(self):
        # Each codepoint represents four bits. I got the layout from the Solar
        # Jetman Password Generator, but I'm *sure* there's a better way
        # to model what it's doing. The game's password system can't possibly
        # be this stupid.

        cp = [0] * 12
        cp[ 0] = self.lives
        cp[ 1] = self.scoredigit(0)
        cp[ 2] = self.level // 4  # upper two(?) bits of level
        cp[ 3] = 0  # checksum 1
        cp[ 4] = self.scoredigit(2)
        cp[ 5] = self.scoredigit(1)
        cp[ 6] = self.scoredigit(3)
        cp[ 7] = self.scoredigit(4)
        cp[ 8] = (
                    # upper two bits of code 8 are the lower two bits of level.
                    # The other two bits are flags.
                    self.level % 4 << 2
                    | self.map << 1
                    | self.supermap
                )
        cp[ 9] = 0  # checksum 2
        cp[10] = (
                    # upper two bits of code 10 are ship, lower two are flags
                    self.ship << 2
                    | self.shields << 1
                    | self.thrusters
                )
        cp[11] = self.scoredigit(5)

        chk1 = ((cp[0] ^ cp[1]) + cp[2] ^ cp[4]) + cp[5]
        chk2 = ((cp[6] ^ cp[7]) + cp[8] ^ cp[10]) + cp[11]
        chk2 += int(chk1 >= 16)
        chk1 += chk2 // 16
        cp[3] = chk1 % 16
        cp[9] = chk2 % 16
        return cp

    def scoredigit(self, i):
        # NOTE: i=0 is least significant digit
        return self.score // 10**i % 10

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
