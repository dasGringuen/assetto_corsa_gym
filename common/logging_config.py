import logging
import sys
import os

format = "%(asctime)s[%(levelname)-s] %(name)s %(message)s"

"""
Examples:

# the main module configures as follows
import logging_config as logging_config
logging_config.create_logging(level=logging.DEBUG, file_name='log', file_path=run_path)
logging.getLogger().setLevel(logging.INFO)

# each module should have this:
import logging
logger = logging.getLogger(__name__)

# to change level of a submodule
logging.getLogger("submodules.sub").setLevel(logging.DEBUG)

# good to have the logger always in the same place as the script + in the archive...
# e.g. next to main.py and in resuls
logging_config.add_file_handler("secong.log")
"""
format = "%(asctime)s[%(levelname)-s] %(name)s %(message)s"

def create_logging(level=logging.INFO, file_name=None, file_path=None):
    handlers = None

    if file_path:
        file_name = 'log.txt'
        file_name = os.path.join(file_path, file_name)

    if file_name:
        handlers = [
            logging.FileHandler(file_name),
            logging.StreamHandler(),
        ]
    l = logging.getLogger()     # root logger
    for hdlr in l.handlers[:]:  # remove existing handlers
        l.removeHandler(hdlr)

    logging.basicConfig(level=level, format=format, handlers=handlers)

def add_file_handler(file_name):
    hdlr = logging.FileHandler(file_name)
    hdlr.setFormatter(logging.Formatter(format))
    logging.getLogger().addHandler(hdlr)