import datetime
import pickle
import os

import logging
logger = logging.getLogger(__name__)

class Telemetry(object):
    def __init__(self, subfolder="telemetry"):
        self.telemetry = []
        self.recording = False
        self.static_info = {}
        # Get the current timestamp in the specified format
        self.output_path = os.path.abspath(os.getcwd()) + os.sep + subfolder + os.sep
        # create directory if it does not exist
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def start_recording(self):
        self.recording = True
        self.telemetry = []
        self.steps = 0

    def stop_recording(self):
        self.recording = False

    def step(self, sample):
        if self.recording:
            self.steps += 1
            sample['steps'] = self.steps
            self.telemetry.append(sample)

    def set_static_info(self, static_info):
        self.static_info = static_info

    def save_telemetry(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_name = self.output_path + 'telemetry_' + timestamp + '.pkl'
        logger.info("[MAIN] Saving telemetry with {} steps to file: {}".format(len(self.telemetry), file_name))
        with open(file_name, 'wb') as f:
            pickle.dump({"telemetry":self.telemetry,
                         "static_info": self.static_info,
                         },
                         f,
                         pickle.HIGHEST_PROTOCOL)