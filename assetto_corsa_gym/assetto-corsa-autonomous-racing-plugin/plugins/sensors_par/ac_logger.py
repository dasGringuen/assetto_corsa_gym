import ac
import time
import traceback
import datetime

import logging
logger = logging.getLogger(__name__)


class ACHandler(logging.Handler):
    """
    Custom logging handler that logs messages to ac.log and ac.console.
    """
    def emit(self, record):
        log_entry = self.format(record)
        ac.log(log_entry)
        ac.console(log_entry)

def setup_logger(file_name=None, file_path='.'):
    # ac handler
    ac_handler = ACHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ac_handler.setFormatter(formatter)

    handlers = [
        ac_handler
    ]
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s[%(levelname)-4.4s] %(name)s %(message)s",
                        handlers=handlers)