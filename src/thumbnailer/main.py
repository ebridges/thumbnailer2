#!/usr/bin/env python3

from sys import argv
from argparse import ArgumentParser
from logging import debug, info

from thumbnailer.image import resize
from thumbnailer.util import configure_logging, DEFAULT_WIDTH, DEFAULT_HEIGHT


def app(args):
    with open(args.filename, mode='rb') as f:
        resize(f.read(), args.filename, args.width, args.height)


def main(argv):
    parser = ArgumentParser(prog=argv[0])
    parser.add_argument('-v', '--verbose', default=False, action='store_true')
    parser.add_argument('-f', '--filename')
    parser.add_argument(
        '-dw', '--width', type=int, required=False, default=DEFAULT_WIDTH
    )
    parser.add_argument(
        '-dh', '--height', type=int, required=False, default=DEFAULT_HEIGHT
    )

    args = parser.parse_args()
    configure_logging(args.verbose)

    debug(args)

    app(args)


if __name__ == '__main__':
    main(argv)
