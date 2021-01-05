from .password import Password, InvalidPassword
from . import text

try:
    from .version import version
except ImportError:
    version = 'UNKNOWN'
