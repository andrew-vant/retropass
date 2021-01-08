import codecs
import logging
from functools import lru_cache

from .util import libroot

log = logging.getLogger(__name__)

def load(name, f):
    """ Load a text codec from a file-like object"""

    c2b={}
    b2c={}

    for line in f:
        if not line.strip() or line.startswith('#'):
            continue
        line = line.rstrip('\n')
        byte, char = line.split('=')
        byte = int(byte, 16)
        c2b[char] = byte
        b2c[byte] = char

    assert len(c2b) == len(b2c)
    if not c2b:
        raise ValueError(f"text table for {name} appears to be empty")

    def decode(_bytes):
        s = ''.join(b2c[byte] for byte in _bytes)
        return (s, len(_bytes))

    def encode(s):
        _bytes = bytes(c2b[char] for char in s)
        return (_bytes, len(s))

    ci = codecs.CodecInfo(encode, decode)
    return ci


@lru_cache()
def lookup(name):
    """ Look up a text codec by name

    This is registered as a codec search function, so it shouldn't need to be
    called directly."""

    path = f'{libroot}/game/{name}.tbl'
    try:
        with open(path) as f:
            return load(name, f)
    except FileNotFoundError as ex:
        log.debug(ex)
    return None

codecs.register(lookup)
