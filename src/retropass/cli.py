import sys
import os
import argparse
import logging
from functools import partial

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
    addflag = partial(parser.add_argument, action='store_true')

    addflag("-v", "--verbose", help="verbose logging")
    addflag("-d", "--debug", help="debug logging")

    args = parser.parse_args()
    level = (logging.DEBUG if args.debug
             else logging.INFO if args.verbose
             else logging.WARN)
    lfmt = '%(levelname)s\t%(module)s:%(lineno)d\t%(message)s'
    logging.basicConfig(level=level, format=lfmt)
    log.debug("debug logging on")
    log.info("verbose logging on")

    pw = rp.Password.make('metroid')
    pw.taken_marumari = True
    pw.has_marumari = True
    log.debug(pw.data)
    print(pw)


if __name__ == '__main__':
    main()
