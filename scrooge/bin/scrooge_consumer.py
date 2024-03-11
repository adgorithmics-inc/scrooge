#!/usr/bin/env python

import logging
import os
import sys

from scrooge.constants import WORKER_PROCESS
from scrooge.consumer import Consumer
from scrooge.consumer_options import ConsumerConfig, OptionParserHandler
from scrooge.utils import load_class


def err(s):
    sys.stderr.write("\033[91m%s\033[0m\n" % s)


def load_scrooge(path):
    try:
        return load_class(path)
    except:
        cur_dir = os.getcwd()
        if cur_dir not in sys.path:
            sys.path.insert(0, cur_dir)
            return load_scrooge(path)
        err("Error importing %s" % path)
        raise


def consumer_main():
    parser_handler = OptionParserHandler()
    parser = parser_handler.get_option_parser()
    options, args = parser.parse_args()

    if len(args) == 0:
        err("Error:   missing import path to `Scrooge` instance")
        err("Example: scrooge_consumer.py app.queue.scrooge_instance")
        sys.exit(1)

    options = {k: v for k, v in options.__dict__.items() if v is not None}
    config = ConsumerConfig(**options)
    config.validate()

    if sys.platform == "win32" and config.worker_type == WORKER_PROCESS:
        err('Error:  scrooge cannot be run in "process"-mode on Windows.')
        sys.exit(1)

    scrooge_instance = load_scrooge(args[0])

    # Set up logging for the "scrooge" namespace.
    logger = logging.getLogger("scrooge")
    config.setup_logger(logger)

    consumer = scrooge_instance.create_consumer(**config.values)
    consumer.run()


if __name__ == "__main__":
    if sys.version_info >= (3, 8) and sys.platform == "darwin":
        import multiprocessing

        try:
            multiprocessing.set_start_method("fork")
        except RuntimeError:
            pass
    consumer_main()
