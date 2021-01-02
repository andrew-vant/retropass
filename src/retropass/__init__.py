from .password import Password
from . import text

try:
    from .version import version
except ImportError:
    version = 'UNKNOWN'
