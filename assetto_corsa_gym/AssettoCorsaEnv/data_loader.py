import glob
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
import yaml

import logging
logger = logging.getLogger(__name__)

from AssettoCorsaEnv.brake_map import BrakeMap

def read_yml(f):
    with open(f, 'r') as file:
        return yaml.safe_load(file)

def seconds_to_mm_ss_mmm(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:2d}:{remaining_seconds:06.3f}"

class DataLoader():
    def __init__(self, env, data_set_path, steer_map_file, brake_map_file):
        self.env = env
        self.trajectories_paths =  sorted( glob.glob(data_set_path  + '/*.pkl' ) )
        self.trajectories_count = len(self.trajectories_paths)
        assert self.trajectories_count > 0, f"No trajectories found in {data_set_path}"
        logger.info(f"Found {self.trajectories_count} trajectories in the path: {data_set_path}")

        self.trajectory_number = 0
        self.current_step = 0
        self.prev_abs_actions = None

        self.brake_map = BrakeMap.load(brake_map_file)
        self.steer_max = pd.read_csv(steer_map_file).values[1,1]

    def get_actions_from_state(self, state):
        steer = state["steerAngle"] / self.steer_max
        pedal = (state["accStatus"] - 0.5) * 2  # 0,1 -> -1,1
        brake = self.brake_map.get_x(state["brakeStatus"]).item() # map
        return np.array( [steer, pedal, brake] )

    def load_next_trajectory(self):
        load_path = self.trajectories_paths[self.trajectory_number]
        assert Path(load_path).exists(), f"Trajectory file not found: {load_path}"
        try:
            with open(load_path, 'rb') as f:
                t = pickle.load(f)
                self.trajectory = t["states"]
                self.static_info = t["static_info"]
                #print(f"Loaded trajectory number: {self.trajectory_number}/{self.trajectories_count - 1} with len: {len(self.trajectory)}")
                self.trajectory_number += 1
                self.current_step = 0
        except Exception:
            logger.error(f"Error loading trajectory: {load_path}")
            raise
        #logger.info(f"found n steps {len(self.trajectory)}")

    def read_step(self):
        state = self.trajectory[self.current_step]
        history = self.trajectory[:self.current_step] # get the history seen so far
        current_abs_actions = self.get_actions_from_state(state)

        if self.current_step == 0:
            self.prev_abs_actions = current_abs_actions

        actions = self.env.inverse_preprocess_actions(self.prev_abs_actions, current_abs_actions)
        self.prev_abs_actions = current_abs_actions

        # abs values or relative
        self.current_actions = np.array([current_abs_actions[0],
                                         current_abs_actions[1],
                                         current_abs_actions[2]], dtype='float32')
        self.action = np.array( [actions[0],
                                 actions[1],
                                 actions[2]], dtype='float32')

        self.state = state
        # re build the observations and the reward using the current environment settings
        self.obs, self.actions_diff = self.env.get_obs(state, history)
        self.reward = self.env.get_reward(state, self.actions_diff).item()

        done = False
        terminated = False
        if self.state["out_of_track"]: # or AC oot
            terminated = True
            #self.reward = .0
            # don't end the episode on oot , human laps are full of them
            # but we set the termination signal which is needed to train the model
        self.current_step += 1
        if self.current_step == len(self.trajectory) + 1:
            done = True
        self.info = {"terminated": float(terminated)}
        self.done = float(done)

    def reset(self):
        self.load_next_trajectory()
        self.read_step()
        return self.obs

    def act(self):
        self.read_step()
        return self.action

    def step(self, action):
        return self.obs, self.reward, self.done, self.info

    def get_task_id(self):
        return self.env.get_task_id()

def get_path_for_track_car(dataset_path, file, track, car):
    data = read_yml(file)
    paths = data[track][car]
    paths = [dataset_path / Path(f"{track}/{car}") / p["id"] for p in paths]
    return paths

def get_all_paths_in_file(file, dataset_path, filter_tags={}, filter_track=None, filter_car=None):
    data = read_yml(file)
    all_paths = []

    for track, cars in data.items():
        if filter_track and track != filter_track:
            continue
        for car, entries in cars.items():
            if filter_car and car != filter_car:
                continue
            for entry in entries:
                # Check if entry matches all specified filter tags
                if all(entry.get(tag) == value for tag, value in filter_tags.items()):
                    path = dataset_path / Path(f"{track}/{car}") / entry["id"]
                    all_paths.append((path.as_posix() + "/laps/", car, track))
    return all_paths

def lap_times_list(df):
    lap_times = []
    for i in list(set(df["LapCount"])):
        if i == 0: # discard out lap
            continue
        l = df[df["LapCount"] == i]
        t = l["lastLapTime"].values[-1]
        lap_times.append(t)
    return lap_times