#!/usr/bin/env python3

# Modified from Vibhaas' implementation

import logging

from cli.main import cli


logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

if __name__ == "__main__":
    cli()
