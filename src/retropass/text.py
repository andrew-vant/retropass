import os
import codecs
import logging
from glob import glob
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
        byte, char = line.split('=')
        c2b[char] = int(byte, 16)
        b2c[byte] = char

    def decode(_bytes):
        return ''.join(b2c[byte] for byte in _bytes)

    def encode(s):
        return [c2b[char] for char in s]

    ci = codecs.CodecInfo(encode, decode)
    return ci


@lru_cache
def lookup(name):
    """ Look up a text codec by name

    This is registered as a codec search function, so it shouldn't need to be
    called directly."""

    path = f'{libroot}/plugins/{name}.tbl'
    try:
        with open(path) as f:
            return load(name, f)
    except FileNotFoundError as ex:
        log.debug(ex)
    return None

codecs.register(lookup)
