import sys
import argparse
import logging
from functools import partial
from argparse import FileType

import retropass as rp


log = logging.getLogger(__name__)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    desc = "retro game password generator"

    # Check for the version option before normal parsing, so the parser doesn't
    # choke on missing args:
    if "-V" in argv or "--version" in argv:
        print('retropass v' + rp.version)
        sys.exit()

    parser = argparse.ArgumentParser(description=desc)

    addarg = parser.add_argument
    addopt = partial(addarg, nargs='?')
    addflag = partial(addarg, action='store_true')

    addarg("game", choices=rp.Password.supported_games(),
           help="game to generate password for")
    addopt("-c", "--conf", help="file to take settings from", type=FileType())
    addopt("-p", "--password", help="password to decode")
    addflag("-d", "--dump", help="dump resulting settings, or defaults")
    addflag("-v", "--verbose", help="verbose logging")
    addflag("-D", "--debug", help="debug logging")
    addflag("-V", "--version", help="print program version")

    args = parser.parse_args(argv)
    level = (logging.DEBUG if args.debug
             else logging.INFO if args.verbose
             else logging.WARN)
    lfmt = '%(levelname)s\t%(module)s:%(lineno)d\t%(message)s'
    logging.basicConfig(level=level, format=lfmt)
    log.debug("debug logging on")
    log.info("verbose logging on")

    try:
        pw = rp.Password.make(args.game, args.password, args.conf)
    except rp.InvalidPassword as ex:
        log.error(ex)
        sys.exit(2)

    if args.dump or args.password:
        print(pw.dump())
    else:
        print(pw)

if __name__ == '__main__':
    main()
