import abc
from collections import Counter
from collections.abc import Mapping
from itertools import chain

from bitarray import bitarray
from bitarray.util import ba2int, int2ba, ba2hex, zeros

from .util import rotate, chunk, readtsv, libroot


class Field:
    """ Attributes of a password data field """
    def __init__(self, fid, offset, width, _type='uint', group='misc',
                 order=0, desc='', **kwargs):
        if isinstance(offset, str):
            offset = int(offset, 0)
        if isinstance(width, str):
            width = int(width, 0)
        if 'type' in kwargs:
            _type = kwargs['type']

        self.fid = fid
        self.offset = offset
        self.width = width
        self.group = group
        self.order = order
        self.desc = desc
        self.type = _type

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
    _initialized = False
    _games = {}

    # These must be provided by subclasses
    gid = None  # Game ID
    fields = None

    def __init_subclass__(cls):
        if not cls.gid:
            raise ValueError(f"{cls} didn't specify game name")
        cls._games[cls.gid] = cls

    @classmethod
    def make(cls, gid):
        return cls._games[gid]()

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
        return ba2int(self.data[field.slice])

    def __setattr__(self, name, value):
        if not self._initialized:
            object.__setattr__(self, name, value)
        elif name not in self.fields:
            raise AttributeError(f"No such field: {name}")
        else:
            field = self.fields[name]
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

    def dump(self):
        cw = max(len(fid) for fid in self.fields) + 2
        fmt = '{fid:{width}}{value}\n'
        out = ''
        for fid, value in sorted(self.items()):
            out += fmt.format(fid=fid+':', width=cw, value=self[fid])
        return out


class MetroidPassword(Password):
    gid = 'metroid'
    fields = Field.gamefields(gid)

    def __init__(self):
        self.shift = 0
        super().__init__()

    @property
    def bits(self):
        bits = rotate(self.data, self.shift)
        bits += int2ba(self.shift, 8, 'little')
        bits += int2ba(self.checksum, 8, 'little')
        return bits

    @property
    def checksum(self):
        _bytes = self.data.tobytes()
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

    def __repr__(self):
        return ba2hex(self.bits)

    def __str__(self):
        pw = bytes(self.codepoints).decode(self.gid)
        return ' '.join(chunk(pw, 6))
