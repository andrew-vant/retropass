import sys
import os
import argparse
import logging
from functools import partial
from argparse import FileType

import retropass as rp
import retropass.util as util


log = logging.getLogger(__name__)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    desc = "retro game password generator"
    desc = "metroid password generator"

    parser = argparse.ArgumentParser(description=desc)

    addarg = parser.add_argument
    addopt = partial(addarg, nargs='?')
    addflag = partial(addarg, action='store_true')

    addarg("game", help="game to generate password for")
    addopt("conf", help="file to take settings from", type=FileType())
    addflag("-d", "--dump", help="dump resulting settings, or defaults")
    addflag("-v", "--verbose", help="verbose logging")
    addflag("-D", "--debug", help="debug logging")

    args = parser.parse_args()
    level = (logging.DEBUG if args.debug
             else logging.INFO if args.verbose
             else logging.WARN)
    lfmt = '%(levelname)s\t%(module)s:%(lineno)d\t%(message)s'
    logging.basicConfig(level=level, format=lfmt)
    log.debug("debug logging on")
    log.info("verbose logging on")

    pw = rp.Password.make(args.game)
    if args.conf:
        for line in args.conf:
            # Skip comments and blank lines
            if line.startswith("#") or not line.strip():
                continue
            k, v = (part.strip() for part in line.split(":"))
            pw[k] = int(v, 0)

    if args.dump:
        print(pw.dump())
    else:
        print(pw)


if __name__ == '__main__':
    main()
