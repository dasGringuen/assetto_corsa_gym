import pickle
import time
import os
import csv
import datetime
from sim_info import info

import logging
logger = logging.getLogger(__name__)

class Profiler:
    def __init__(self, enabled):
        self.enabled = enabled
        self.output_path = os.path.abspath(os.getcwd()) + os.sep + "profiler" + os.sep
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        logger.info("Profiler enabled: {} {}".format(self.enabled, self.output_path))
        self.reset()

    def reset(self):
        self.events = []

    def enable_profiler(self, enable=True):
        """Enable or disable the profiler."""
        self.enabled = enable

    def add_event(self, event_name):
        """Add an event with a timestamp if the profiler is enabled."""
        if self.enabled:
            self.events.append({"event_type": event_name,
                                "t_perf_counter": time.perf_counter(),
                                "t_iCurrentTime": info.graphics.iCurrentTime,
                                "packetId": info.graphics.packetId})

    def get_events(self):
        """Retrieve all logged events."""
        return self.events

    def dump_to_pickle(self, file_path):
        if len(self.events):
            """Serialize the events list to a pickle file."""
            with open(file_path, 'wb') as file:
                pickle.dump(self.events, file)

    def save_to_csv(self):
        if self.enabled:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_name = self.output_path + 'profiler_' + timestamp + '.csv'
            with open(file_name, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["event_type", "t_perf_counter", "t_iCurrentTime", "packetId"])
                writer.writeheader()
                for event in self.events:
                    writer.writerow(event)
            logger.info("Profiler data saved to: {}".format(file_name))