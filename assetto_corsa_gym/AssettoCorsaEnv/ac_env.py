import os
import sys
import numpy as np
import pandas as pd
import pickle
from gym import spaces
from gym import Env
from gym.spaces import Box
from gym import utils as gym_utils
from datetime import datetime
import time
import yaml
import json
from pathlib import Path

from AssettoCorsaEnv.ac_client import Client
from AssettoCorsaEnv.track import Track
from AssettoCorsaEnv.reference_lap import ReferenceLap
import AssettoCorsaEnv.sensors_ray_casting as sensors_ray_casting
from AssettoCorsaEnv.sensors_ray_casting import MAX_RAY_LEN
from AssettoCorsaEnv.gap import get_gap

import torch

import logging
logger = logging.getLogger(__name__)

# filter the racing line to this circle
RACING_LINE_DIAMETER_CROP = 300.
PAST_ACTIONS_WINDOW = 3

# Curvature look ahead
CURV_LOOK_AHEAD_DISTANCE = 300. # METERS
CURV_LOOK_AHEAD_VECTOR_SIZE = 12 # SIZE OF THE VECTOR
CURV_NORMALIZATION_CONSTANT = 0.1

# target speed
TARG_SPEED_LOOK_AHEAD_VECTOR_SIZE = CURV_LOOK_AHEAD_VECTOR_SIZE
TARG_SPEED_LOOK_AHEAD_DISTANCE = CURV_LOOK_AHEAD_DISTANCE

# episode termination
TERMINAL_LIMIT_PROGRESS_SPEED  = 1.0  # [m/s], episode terminates if car is running slower than this limit
TERMINAL_JUDGE_TIMEOUT = 10.       # If after this number of seconds still no progress, terminate the episode. In seconds

TOP_SPEED_MS = 80.

def get_date_timestemp():
    return datetime.now().strftime('%Y%m%d_%H%M%S.%f')[:-3]

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def to_pickle(obj, file, verbose=False):
    if verbose: print('saving to..', file)
    with open(file, 'wb') as f: pickle.dump(obj, f)

def convert_to_seconds(time_str):
    """
    Convert time from "minutes:seconds:milliseconds" format to seconds with decimals.

    :param time_str: A string representing the time in "minutes:seconds:milliseconds" format.
    :return: The time converted to seconds (as a float).
    """
    parts = time_str.split(":")
    if len(parts) != 3:
        raise ValueError("Time string must be in 'minutes:seconds:milliseconds' format")

    minutes = int(parts[0])
    seconds = int(parts[1])
    milliseconds = int(parts[2])

    return minutes * 60 + seconds + milliseconds / 1000

class TaskIdsIndexer:
    def __init__(self, tracks, cars):
        self.tracks = tracks
        self.cars = cars
        self.combination_indices = {}
        self._generate_indices()
        self.num_tasks = self.get_number_of_tasks()

    def _generate_indices(self):
        """Private method to generate indices for each track and car combination."""
        index = 0
        for track in self.tracks:
            for car in self.cars:
                key = f"{track}_{car}"
                self.combination_indices[key] = index
                index += 1

    def get_index(self, track, car):
        """Method to get the index of a specific track and car combination."""
        key = f"{track}_{car}"
        return self.combination_indices.get(key, -1)  # Return -1 if the combination does not exist

    def get_number_of_tasks(self):
        """Method to return the total number of unique track and car combinations."""
        return len(self.combination_indices)

    def get_task_one_hot(self, task_id):
        """Method to get the one-hot encoding of a specific track and car combination."""
        assert task_id != -1, "Invalid task ID"
        task_one_hot = np.zeros(self.num_tasks)
        task_one_hot[task_id] = 1.
        return task_one_hot

class AssettoCorsaEnv(Env, gym_utils.EzPickle):
    # List of tracks and cars when using task IDs
    tracks = [
        "ks_barcelona-layout_gp",
        "ks_red_bull_ring-layout_gp",
        "monza",
        "indianapolis_sp"
    ]

    cars = [
        "dallara_f317",
        #"bmw_z4_gt3"
    ]

    obs_channels_info = {
        'speed': TOP_SPEED_MS,  # km/h
        'gap': 10.,
        'LastFF': 1.,
        'RPM': 10000.,
        'accelX': 5.,
        'accelY': 5.,

        'angular_velocity_x': np.pi,
        'angular_velocity_y': np.pi,
        'angular_velocity_z': np.pi,
        'local_velocity_x': TOP_SPEED_MS,
        'local_velocity_y': 20.,
        'local_velocity_z': 5.,
        'SlipAngle_fl': 25.,
        'SlipAngle_fr': 25.,
        'SlipAngle_rl': 25.,
        'SlipAngle_rr': 25.,
        'wheel_speed_rr': TOP_SPEED_MS / 3.6,
        'wheel_speed_rl': TOP_SPEED_MS / 3.6,
        'wheel_speed_fr': TOP_SPEED_MS / 3.6,
        'wheel_speed_fl': TOP_SPEED_MS / 3.6,
        'tyre_slip_ratio_fl': 1.,
        'tyre_slip_ratio_fr': 1.,
        'tyre_slip_ratio_rl': 1.,
        'tyre_slip_ratio_rr': 1.,
        'Dy_rr': 2.,    # lateral grip
        'Dy_rl': 2.,    # very noisy. Goes to zero when the wheel is spinning
        'Dy_fr': 2.,
        'Dy_fl': 2.,
        'LapCount': 1.,
        'LapDist': 1.,
        # commands feedback
        'steerAngle': 450,
        'accStatus': 1.,
        'brakeStatus': 1.,
        'actualGear': 8.,
    }

    obs_enabled_channels = [
        'speed',
        'gap',
        'LastFF',
        'RPM',
        'accelX',
        'accelY',
        'actualGear',
        #'angular_velocity_x',
        'angular_velocity_y',
        #'angular_velocity_z',
        'local_velocity_x',
        'local_velocity_y',
        #'local_velocity_z',
        'SlipAngle_fl',
        'SlipAngle_fr',
        'SlipAngle_rl',
        'SlipAngle_rr',
        # 'tyre_slip_ratio_fl',
        # 'tyre_slip_ratio_fr',
        # 'tyre_slip_ratio_rl',
        # 'tyre_slip_ratio_rr',
        # 'wheel_speed_rr',
        # 'wheel_speed_rl',
        # 'wheel_speed_fr',
        # 'wheel_speed_fl',
        # 'Dy_rr',
        # 'Dy_rl',
        # 'Dy_fr',
        # 'Dy_fl',
    ]

    obs_extra_enabled_channels = [
        'local_velocity_x',
        'local_velocity_y',
        'angular_velocity_y',
        'steerAngle',
        'accStatus',
        'brakeStatus',
        'world_position_x',
        'world_position_y',
        'yaw'
    ]


    def __init__(self, config,
                 output_path: None,
                 ac_configs_path= None,
                 torch_device = None,
                 enable_out_of_track_calculation=True,
                 max_episode_steps=None,
                 max_gap=None,
                 gap_const = 12., # gap penalization
                 penalize_gap = True,
                 save_observations=True,
                 verbose=False
                 ):
        """ Assetto Corsa External Driver.
        """
        gym_utils.EzPickle.__init__(self)
        self.config = config
        self.output_path = output_path
        self.ctrl_rate = self.config.ego_sampling_freq # check
        self.track_name = self.config.track
        self.car_name = self.config.car
        self.ac_configs_path = ac_configs_path
        self.use_target_speed = self.config.use_target_speed
        self.torch_device = torch_device
        self.use_relative_actions = self.config.use_relative_actions
        self.enable_sensors = self.config.enable_sensors
        self.enable_out_of_track_calculation = enable_out_of_track_calculation
        self._max_episode_steps = max_episode_steps
        self.enable_low_speed_termination = self.config.enable_low_speed_termination
        self.max_gap = max_gap
        self.gap_const = gap_const
        self.penalize_gap = penalize_gap
        self.save_observations = save_observations
        self.recover_car_on_done = self.config.recover_car_on_done
        self.enable_out_of_track_termination = self.config.enable_out_of_track_termination
        self.add_previous_obs_to_state = self.config.add_previous_obs_to_state
        self.send_reset_at_start = self.config.send_reset_at_start
        self.max_steer_rate = self.config.max_steer_rate
        self.use_obs_extra = self.config.use_obs_extra
        self.use_reference_line_in_reward = self.config.use_reference_line_in_reward

        # from the config
        self.use_ac_out_of_track = self.config.use_ac_out_of_track
        self.enable_out_of_track_penalty = self.config.enable_out_of_track_penalty # oot penalization in the reward function

        self.penalize_actions_diff = config.penalize_actions_diff
        self.penalize_actions_diff_coef = config.penalize_actions_diff_coef

        self.max_laps_number = self.config.max_laps_number

        self.tracks_path = os.path.join(self.ac_configs_path, "tracks")
        self.cars_paths = os.path.join(self.ac_configs_path, "cars")

        self.tracks_config = load_yaml(os.path.join(self.tracks_path, "config.yaml"))
        self.set_track(self.track_name)

        # task id
        self.tasks_ids = TaskIdsIndexer(self.tracks, self.cars)
        self.current_task_id = self.tasks_ids.get_index(self.track_name, self.car_name)

        self.states = []      # some extra channels calculated. Without initialization
        self.history_obs = []  # history of observations
        self.episodes_stats = []
        self.info = {}

        self.total_steps = 0
        self.n_episodes = 0
        self.ep_steps = 0
        self.ep_reward = 0.
        self.stats_saved = False

        self.client = Client(self.config)
        self.static_info = {}
        self.ac_mod_config = {}

        if self.output_path:
            self.laps_path = self.output_path + os.sep + "laps" + os.sep
            os.makedirs(self.laps_path, exist_ok=True)

        self.dt = 1. / self.ctrl_rate

        # load track  # TODO: use pytorch?
        self.track = Track(track_file_path=self.track_file, track_grid_file=self.track_grid_file,
                           torch_device=None) # Note: send the torch device to find the grid using pytorch

        #
        self.ref_lap = ReferenceLap(self.ref_lap_file, use_target_speed=self.use_target_speed)
        self.racing_line = self.ref_lap.get_racing_line_time()
        if torch_device:
            self.racing_line_torch =  torch.tensor(self.racing_line, device=torch_device, dtype=torch.float)

        if self.use_target_speed:
            self.target_speed = self.ref_lap.get_channel_time("target_speed")

        self.ref_lap_dist_channel_time = self.ref_lap.get_channel_time("lapDistance")

        if self.enable_sensors:
            self.sensors = sensors_ray_casting.SensorsRayCasting(self.track.right_border_x, self.track.right_border_y,
                                                             self.track.left_border_x, self.track.left_border_y)

        #
        # for gym
        #
        # Define physical and simulator parameters for each channel.
        steer_map_file = Path(self.cars_paths) / self.car_name / 'steer_map.csv'
        self.max_steer_deg = pd.read_csv(steer_map_file).values[1,1]
        self.norm_steer_at_max = pd.read_csv(steer_map_file).values[1,0]

        # Original controls_rate_limit (in deg/s scaled per time step)
        self.controls_rate_limit = np.array([[-self.max_steer_rate, self.max_steer_rate],
                                              [-1200/100, 1200/100],  # pedal: (falling edge)
                                              [-1200/100, 1200/100],  # brake: (release/press)
                                             ]) * (1/self.ctrl_rate)


        # Conversion factor (deg per normalized unit) for steering.
        self.steering_scale_factor = self.max_steer_deg / self.norm_steer_at_max
        # For pedal and brake: full range is already [0,1].
        # Create a per-channel scale factor vector.
        self.controls_scale_factor = np.array([self.steering_scale_factor, 1.0, 1.0])
        # Adjust the rate-limit vector per channel (element-wise division along the second axis)
        self.adjusted_controls_rate_limit = self.controls_rate_limit / self.controls_scale_factor[:, np.newaxis]

        # Now, set the absolute limits for the simulator.
        # For steering, use the normalized value corresponding to max steering.
        self.controls_min_values = np.array([-self.norm_steer_at_max, -1.0, -1.0])
        self.controls_max_values = np.array([ self.norm_steer_at_max,  1.0,  1.0])

        # actions space is always -1 to 1 for most algorithms
        self.action_dim = 3
        self.action_space = Box(low=np.array([-1.0, -1.0, -1.0]), high=np.array([1.0, 1.0, 1.0]))

        state_dim = len( self.obs_enabled_channels )
        if self.enable_sensors:
            state_dim += self.sensors.number_of_rays
        self.previous_obs_to_state_dim = state_dim
        if self.add_previous_obs_to_state:
            state_dim  += (PAST_ACTIONS_WINDOW * self.previous_obs_to_state_dim)
            logger.info(f"Adding previous obs to state {self.previous_obs_to_state_dim}*{PAST_ACTIONS_WINDOW} = {state_dim}")
        state_dim += CURV_LOOK_AHEAD_VECTOR_SIZE
        state_dim += (PAST_ACTIONS_WINDOW * 3)
        if self.use_target_speed:
            state_dim += TARG_SPEED_LOOK_AHEAD_VECTOR_SIZE
        if self.config.enable_task_id_in_obs:
            state_dim += self.tasks_ids.get_number_of_tasks()

        # action that was applied when the current state was read
        state_dim += 3
        # out of track in the state
        state_dim += 1
        self.state_dim = state_dim

        self.obs_shape = (self.state_dim,)
        if self.use_obs_extra:
            self.obs_extra_shape = (len(self.obs_extra_enabled_channels),)  # (features,)
        else:
            self.obs_extra_shape = None

        if verbose:
            logger.info(f"enable_sensors {self.enable_sensors}")
            logger.info(f"use_relative_actions {self.use_relative_actions}")
            logger.info(f"use_target_speed {self.use_target_speed}")
            logger.info(f"use_ac_out_of_track: {self.use_ac_out_of_track}")
            logger.info(f"recover_car_on_done: {self.recover_car_on_done}")
            logger.info(f"enable_out_of_track_termination: {self.enable_out_of_track_termination}")
            logger.info(f"enable_low_speed_termination: {self.enable_low_speed_termination}")
            logger.info(f"enable_out_of_track_penalty: {self.enable_out_of_track_penalty}")
            logger.info(f"enable_task_id_in_obs: {self.config.enable_task_id_in_obs}")
            logger.info(f"track: {self.config.track}")
            logger.info(f"car: {self.config.car}")
            if self.config.enable_task_id_in_obs:
                logger.info(f"task_id: {self.current_task_id} num_tasks: {self.tasks_ids.get_number_of_tasks()}")

        logger.info(f"state_dim {self.state_dim}")
        logger.info(f"action_space: {self.action_space}")

        high = np.full((self.state_dim, ), np.inf)
        low = np.full((self.state_dim, ), -np.inf)
        self.observation_space = Box(low=low, high=high)

        # scale and obs channels
        self.obs_channels_scales = np.array([self.obs_channels_info[ch] for ch in self.obs_enabled_channels])
        if verbose:
            logger.info("Channels in the observation")
            for ch in self.obs_enabled_channels:
                logger.info("%s: scale %f" % (ch, self.obs_channels_info[ch]))

        # needed for stable baselines
        self.reward_range = (-np.inf, np.inf)
        self.metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': 30}

        self.is_metaworld = False

    def set_reset_state(self, send_reset_at_start):
        self.send_reset_at_start = send_reset_at_start

    def update_racing_line(self, x, y):
        # use a cropped version of the racing line => update the gpu as well
        self.racing_line = self.ref_lap.get_racing_line_time()
        self.racing_line[np.sqrt( (self.racing_line[:,0] - x)**2 + (self.racing_line[:,1] - y)**2 ) < RACING_LINE_DIAMETER_CROP]
        if self.torch_device:
            self.racing_line_torch = torch.tensor(self.racing_line, device=self.torch_device, dtype=torch.float)

    def preprocess_actions(self, actions, current_actions):
        if self.use_relative_actions:
            # Fully vectorized update: scale each action by the adjusted per-channel rate limit.
            new_actions = current_actions + actions * self.adjusted_controls_rate_limit[:, 1]
        else:
            new_actions = actions
        return np.clip(new_actions, self.controls_min_values, self.controls_max_values)

    def inverse_preprocess_actions(self, prev_abs_actions, current_abs_actions):
        if self.use_relative_actions:
            # Use the adjusted rate limit's upper bound for each channel.
            max_delta = self.adjusted_controls_rate_limit[:, 1]
            actions = (current_abs_actions - prev_abs_actions) / max_delta
            return np.clip(actions, -1.0, 1.0)
        else:
            return np.clip(current_abs_actions, self.controls_min_values, self.controls_max_values)

    def set_actions(self, actions):
        """
        Apply the actions to the sim right away. The step function can be called later
        """
        # get state from the sim
        self.raw_actions = actions.copy()

        # actions are deltas, update current controls
        self.current_actions = self.preprocess_actions(actions, self.current_actions)
        self.actions = self.current_actions

        self.client.controls.set_controls(steer=self.actions[0], acc=self.actions[1], brake=self.actions[2])
        self.client.respond_to_server()

    def step(self, action=None):
        """
        If actions is None, the the policy should set the actions before by calling set_actions

        Blocks until the sim returns the next state
        """
        self.ep_steps += 1
        self.total_steps += 1

        if action is not None:
            self.set_actions(action)

        state = self.client.step_sim()
        state["timestamp_env"] = time.perf_counter()

        self.state, buf_infos = self.expand_state(state)

        # add the current absolute actions to the state
        for i in range(self.action_dim):
            self.state[f'current_action_abs_{i:01d}'] = self.current_actions[i]

        # save input actions
        for i in range(self.action_dim):
            self.state[f'actions_{i:01d}'] = self.raw_actions[i]

        # create obs
        obs, actions_diff = self.get_obs(state, self.states)

        #
        #   Reward
        #
        self.state["reward"] = self.get_reward(self.state, actions_diff).item()

        if (self.ep_steps % 50) == 0:
            logger.debug(f't: {self.ep_steps} speed: {state["speed"]:.2f}, oot: {state["out_of_track"]} '
                         f's: {self.actions[0]:.2f} a: {self.actions[1]:.2f} b: {self.actions[2]:.2f} '
                         f'reward: {state["reward"]:.3f} '
                         f'done: {state["done"]:.0f} LapDist: {state["LapDist"]:.0f} gap: {state["gap"]:.1f} '
                         )

        self.info = buf_infos
        self.ep_reward += self.state["reward"]
        self.states.append(self.state.copy())
        return obs, self.state["reward"], self.state["done"], buf_infos

    def expand_state(self, state):
        state["currentTime"] = state["currentTime"] / 1000.

        # search for the position of the car 2 segments behind and 2 segments ahead
        x = state["world_position_x"]
        y = state["world_position_y"]

        # normalize distance to the racing line multiplied to the track length
        state["LapDist"] = self.track_length * state["NormalizedSplinePosition"]

        self.update_racing_line(x, y)   # get a smaller version to decrease gap computation time

        #
        #   Gap and distance with respect to the middle of the track
        #
        point = np.array([[x, y]])
        gap, rl_point, closest_points, _ = get_gap(point, self.racing_line)

        # closest point in the racing line
        state['rl_point'] = rl_point.item()
        state['gap'] = gap[0]

        if self.enable_out_of_track_calculation:
            state['out_of_track_calc'] = 0.0 if self.track.track_occupancy_grid.is_inside_grid(point).item() > 0. else 1.0
            state['out_of_track_ac'] = 1.0 if state['numberOfTyresOut'] > 2. else 0.0

        if self.use_ac_out_of_track:
            # get oot from AC. If more than two wheels are out of track, then the car is out of track
            state['out_of_track'] = state['out_of_track_ac']
        else:
            # use the out of track from the calculation and not from AC
            state['out_of_track'] = state['out_of_track_calc']

        # sensors
        if self.enable_sensors:
            state["sensors"] = self.get_sensors(state)
            state["dist_to_border"] = state["sensors"].min()
            if state['out_of_track_calc']:
                # if out of track the car can have the track exactly behind it.
                # In this case, the sensors will not detect the track. Get the sensors on the other side
                new_state = state.copy()
                new_state["yaw"] += np.pi # get the sensors on the other side
                new_sensors = self.get_sensors(new_state)
                state["dist_to_border"] = min(state["dist_to_border"], new_sensors.min())

        # TODO implement if needed
        state["going_backwards"] = 0.

        #
        #   Check episode termination
        #
        # end of episode
        done = 0
        buf_infos = {}
        buf_infos['terminated'] = False  # used by TD MPC
        buf_infos['TimeLimit.truncated'] = False

        if state["done"]:
            ### TODO lap ended by AC.. se what to do here
            logger.info("Terminate. Lap ended by Assetto Corsa")
            done = 1

        if state['going_backwards'] > 0.:
            logger.info("Terminate episode. Going backwards")
            buf_infos['terminated'] = True
            done = 1

        if self.enable_out_of_track_termination and state['out_of_track']:
            logger.info("Terminate episode. is_out_of_track")
            logger.info(f"out_of_track. N wheels out: {state['numberOfTyresOut']}. LapDist: {state['LapDist']} x: {x:.2f} y: {y:.2f}")
            buf_infos['terminated'] = True
            done = 1

        if self._max_episode_steps is not None:
            if self.ep_steps > self._max_episode_steps:
                logger.info(f"Terminate episode. Max steps {self.ep_steps}/{self._max_episode_steps}")
                done = 1
                buf_infos['TimeLimit.truncated'] = True

        if self.max_laps_number and self.get_lap_count(self.states) > self.max_laps_number:
            logger.info(f"Terminate episode. Max number of laps reached {self.max_laps_number}")
            done = 1
            buf_infos['TimeLimit.truncated'] = True

        # Episode terminates if the progress of agent is small
        if self.enable_low_speed_termination and state['speed'] < TERMINAL_LIMIT_PROGRESS_SPEED:
            self.termination_counter -= 1
            if self.termination_counter <= 0:
                logger.info("Race stopped. Speed too low")
                buf_infos['terminated'] = True
                done = 1
            # else:
            #     logger.info(f"Low speed. Will terminate in {self.termination_counter}...")
        else:
            self.termination_counter = int(TERMINAL_JUDGE_TIMEOUT * self.ctrl_rate)

        # check gap
        if self.max_gap and np.abs(gap) > self.max_gap:
            logger.info(f"Race stopped. Gap too big ({gap})")
            done = 1

        # extra channels in the info variable
        if self.use_obs_extra:
            buf_infos['obs_extra'] = self.get_extra_observations(state)
        if done:
            # used by SB3 save final observation where user can get it, then reset
            #buf_infos['terminal_observation'] = obs.copy()
            #obs = self.reset()  # only needed when using vecEnv

            if self.recover_car_on_done:
                self.recover_car()

        state.update(buf_infos)
        state["done"] = done
        return state, buf_infos

    def get_extra_observations(self, state):
        return np.array([state[channel] for channel in self.obs_extra_enabled_channels], dtype=np.float32)

    def get_extra_obs_index(self, channel_name):
        return self.obs_extra_enabled_channels.index(channel_name)

    def get_reward(self, state, actions_diff):
        speed = 3.6 * np.array(state['speed'])
        out_of_track = state["out_of_track_calc"]
        dist_to_border = state["dist_to_border"]

        r = speed
        if self.use_reference_line_in_reward:
            r *= ( 1.0 - (np.abs( state["gap"]) / 12.00))
        r /= 300. # normalize

        if self.penalize_actions_diff:
            action_difference_penalty = np.linalg.norm(actions_diff, ord=2)
            r -= action_difference_penalty * self.penalize_actions_diff_coef
        r = r.reshape(-1)  # [N, 1] -> [N]
        return r

    def recover_car(self):
        logger.info("Recover car")
        self.client.controls.set_defaults()
        self.client.respond_to_server()
        self.client.simulation_management.send_reset()

    def reset(self, seed=None, verbose=False):
        self.end_of_episode_stats()
        self.stats_saved = False

        self.n_episodes += 1
        logger.info(f"Reset AC. Episode {self.n_episodes} total_steps: {self.total_steps}")

        if self.n_episodes == 1:
            # get static info only once
            self.static_info = self.client.simulation_management.get_static_info()
            self.track_length = self.static_info["TrackLength"]
            self.ac_mod_config = self.client.simulation_management.get_config()
            if verbose:
                logger.info("Static info:")
                for i in self.static_info:
                    logger.info(f"{i}: {self.static_info[i]}")
                logger.info("AC Mod config:")
                for i in self.ac_mod_config:
                    logger.info(f"{i}: {self.ac_mod_config[i]}")

            if self.config.screen_capture_enable:
                assert self.config.final_image_height == self.ac_mod_config["final_image_height"],\
                    "Config and AC Mod config do not match for final_image_height. Got {} and {}".format(self.config.final_image_height,
                                                                                                        self.ac_mod_config["final_image_height"])
                assert self.config.final_image_width == self.ac_mod_config["final_image_width"],\
                    "Config and AC Mod config do not match for final_image_width. Got {} and {}".format(self.config.final_image_width,
                                                                                                        self.ac_mod_config["final_image_width"])
                assert self.config.color_mode == self.ac_mod_config["color_mode"], \
                    "Config and AC Mod config do not match for color_mode. Got {} and {}".format(self.config.color_mode,
                                                                                                  self.ac_mod_config["color_mode"])

            assert self.config.ego_sampling_freq == self.ac_mod_config["ego_sampling_freq"], "Ego sampling frequency mismatch"
            assert self.static_info["TrackFullName"] == self.track_name, f"Track name mismatch. Running: {self.static_info['TrackFullName']} Configured: {self.track_name}"
            assert self.static_info["CarName"] == self.car_name, f"Track name mismatch. Running: {self.static_info['CarName']} Configured: {self.car_name}"

        self.client.reset(self.send_reset_at_start)

        self.termination_counter = int(TERMINAL_JUDGE_TIMEOUT * self.ctrl_rate)
        self.episode_saved = False
        self.is_out_of_track = False
        self.current_actions = np.array( [0.0, -1.0, -1.0] )
        self.start_actions = np.array( [0.0, -1.0, -1.0] )

        self.ep_steps = 0  # reset steps after flushing the actions

        # flush a few steps. Otherwise the history state will be incomplete
        for _ in range(2):
            obs, _, _, _ = self.step(self.start_actions)

        self.states = []
        obs, _, _, info = self.step(self.start_actions)
        self.info = info

        self.ep_reward = 0.
        self.ep_steps = 0  # reset steps after flushing the actions
        return obs

    def get_info(self):
        return self.info.copy()

    def close(self):
        return self.end()

    def end(self):
        ep_stats = self.end_of_episode_stats()
        self.client.close()
        return ep_stats

    def get_current_image(self):
        return self.client.get_current_image()

    def rand_act(self):
        return torch.from_numpy(self.action_space.sample().astype(np.float32))

    def get_obs(self, state, history=None):
        """
        if history is None use the current episode history, else use the history passed as argument.append()
        """
        def get_basic_obs(state):
            obs = np.array( [state[ch] for ch in self.obs_enabled_channels] )
            obs = obs / self.obs_channels_scales

            if self.enable_sensors:
                obs = np.hstack([obs, state['sensors'] / MAX_RAY_LEN ])
            return obs

        obs = get_basic_obs(state)

        if state["out_of_track"]:
            obs = np.hstack([obs, 1.0])
        else:
            obs = np.hstack([obs, 0.0])

        # add curvature look ahead
        LAC = self.ref_lap.get_curvature_segment(state['LapDist'],
                                                    CURV_LOOK_AHEAD_DISTANCE,       # meters ahead
                                                    CURV_LOOK_AHEAD_VECTOR_SIZE)    # size of the vector downsampled
        obs = np.hstack([obs, LAC / CURV_NORMALIZATION_CONSTANT])


        if history is None:
            history = self.states

        # add previous absolute actions. Not including the current action (the one that got the sim to the current state)
        if len(history) < PAST_ACTIONS_WINDOW:
            filler = np.zeros(PAST_ACTIONS_WINDOW*self.action_dim)
            obs = np.hstack([obs, filler])
            actions_diff = np.zeros(self.action_dim)
        else:
            current_controls_steer_prev = np.array( [history[i]['steerAngle'] / self.obs_channels_info['steerAngle'] for i in range(-PAST_ACTIONS_WINDOW,0) ]) # if PAST_ACTIONS_WINDOW=3; -3, -2, -1
            current_controls_pedal_prev = np.array( [history[i]['accStatus'] for i in range(-PAST_ACTIONS_WINDOW,0) ])
            current_controls_brake_prev = np.array( [history[i]['brakeStatus'] for i in range(-PAST_ACTIONS_WINDOW,0) ])
            obs = np.hstack([obs, current_controls_steer_prev, current_controls_pedal_prev, current_controls_brake_prev])
            actions_diff = np.array([(state['steerAngle']  - history[-1]['steerAngle'])  / self.obs_channels_info['steerAngle'],
                                        (state['accStatus']   -  history[-1]['accStatus']),
                                        (state['brakeStatus'] - history[-1]['brakeStatus'])])

        # add last action to the observation. Action that got the sim to the current state
        obs = np.hstack([obs, state['steerAngle'] / self.obs_channels_info['steerAngle'], state['accStatus'], state['brakeStatus']])

        #
        if self.add_previous_obs_to_state:
            if len(history) < PAST_ACTIONS_WINDOW:
                prev_obs = np.zeros(PAST_ACTIONS_WINDOW * self.previous_obs_to_state_dim)
            else:
                prev_obs = []
                for i in range(-PAST_ACTIONS_WINDOW, 0):
                    prev_obs.append(get_basic_obs(history[i]))
                prev_obs = np.hstack(prev_obs)
            obs = np.hstack([obs, prev_obs])

        if self.config.enable_task_id_in_obs:
            obs = np.hstack([obs, self.tasks_ids.get_task_one_hot(self.get_task_id())])
        return obs, actions_diff

    def render(self):
        pass

    def seed(self, seed=None):
        pass

    def get_task_id(self):
        return self.current_task_id

    def get_sensors(self, state, do_plots=False):
        intersections, vector_lengths, filtered_walls, points, rectangle\
            = self.sensors.get_intersections_and_distances_to_wall(state["world_position_x"], state["world_position_y"], state['yaw'])
        if do_plots:
            sensors_ray_casting.make_plots(self.sensors.scene, filtered_walls, points, intersections, state["world_position_x"],
                                           state["world_position_y"], rectangle, self.sensors.number_of_rays)
        return vector_lengths

    def show_debug_state(self, state, do_plots=True):
        if self.enable_sensors:
            sensors = self.get_sensors(state, do_plots)
            logger.info(f"sensors: {sensors}")
        logger.info(f"gap: {state['gap']}")
        logger.info(f"VehicleSpeed: {state['speed']}")
        logger.info(f"reward: {state['reward']}")

    def end_of_episode_stats(self, verbose=True):
        save_csv = False

        if len(self.states) and self.stats_saved is False:
            ep = pd.DataFrame(self.states)
            if self.save_observations:
                timestamp = f"{self.laps_path}/{get_date_timestemp()}"
                df_states = pd.DataFrame(self.states)
                states_save_path = f"{timestamp}_states.parquet"
                df_states.to_parquet(states_save_path, engine="pyarrow", index=False)
                logger.info(f"Saved raw data to: {states_save_path}")

                if len(self.episodes_stats) == 0:
                    with open(f"{self.laps_path}/{'static_info.json'}", "w") as f:
                        json.dump(self.static_info, f, indent=4)  # Use indent=4 for readability

                if save_csv:
                    save_csv_channels = ['steps', 'currentTime', 'done',
                                         'speed', 'reward', 'gap',
                                         'world_position_y',
                                         'world_position_x',
                                         'RPM',
                                         'steerAngle', 'brakeStatus', 'accStatus', 'actualGear',
                                         'packetId', 'velocity_x', 'velocity_y', 'velocity_z',
                                         'yaw', 'roll', 'angular_velocity_y', 'angular_velocity_x',
                                         'LapCount',  'LapDist', 'going_backwards',
                                         'current_action_abs_0', 'current_action_abs_1', 'current_action_abs_2',
                                         'actions_0', 'actions_1', 'actions_2', 'rl_point', 'out_of_track',
                                         ]
                    ep[save_csv_channels].to_csv(f"{timestamp}_raw_data.csv", index=False)

            # calculate steps lost in the communication with the server
            differences = np.diff(ep.steps.values)
            number_packages_lost = np.sum(differences[differences > 1])
            gap_abs_max = np.abs(ep.gap).max()
            r = { "ep_count": self.n_episodes,
                  "ep_steps":len(ep),
                  "total_steps": self.total_steps,
                  "packages_lost": number_packages_lost,
                  "ep_reward": ep.reward.sum(),
                  "speed_mean": ep.speed.mean(),
                  "speed_max": ep.speed.max(),
                  #"completedLaps": ep.completedLaps.values[-1],
                  "BestLap": ep['BestLap'].values[-1] / 1000.,
                  "terminated": ep.terminated.values[-1]
            }
            for i, lapCount in enumerate(list(set( ep.LapCount ))):
                r[f"LapNo_{i}"] = ep[ep.LapCount == lapCount]["iLastTime"].values[-1] / 1000 # to seconds
            #  BestLap from the dictionary, excluding lap times that are 0 (incomplete laps)
            r["ep_bestLapTime"] = min((time for key, time in r.items() if key.startswith("LapNo_") and time > 0), default=0)
            if verbose:
                logger.info(f"total_steps: {self.total_steps} ep_steps: {self.ep_steps} ep_reward: {r['ep_reward']:6.1f} "
                            f"LapDist: {self.state['LapDist']:6.2f} packages lost {number_packages_lost} BestLap: {r['BestLap']}")
                for i, lapCount in enumerate(list(set( ep.LapCount ))):
                    logger.info(f"LapNo_{i}: {r[f'LapNo_{i}']:6.2f}")
                logger.info(f"ep_bestLapTime: {r['ep_bestLapTime']:6.2f}")
                logger.info(f"speed_mean: {r['speed_mean']:6.2f} speed_max: {r['speed_max']:6.2f} max_abs_gap: {gap_abs_max:6.2f} ep_laps: {len(set(ep.LapCount))}")
                if len(ep) > 10:
                    dt = np.diff( ep.currentTime.values )[1:]
                    logger.info(f"dt avr: {dt.mean():.3f} std: {dt.std():.3f} min: {dt.min():.3f} max: {dt.max():.3f}")
            if number_packages_lost:
                logger.warning(f"Packages lost in the communication with the server. {number_packages_lost} packages lost")

            self.episodes_stats.append(r.copy())
            pd.DataFrame(self.episodes_stats).to_csv(self.output_path + os.sep + "episodes_stats.csv", index=False)
            self.stats_saved = True
            return r
        else:
            return {}

    def get_lap_count(self, states):
        lap_count = sorted( list(set(i["LapCount"] for i in states)) )
        return len(lap_count)

    def get_history(self):
        states = self.states
        return pd.DataFrame(states)

    def load_history(self, file_path):
        """Loads trajectory data, inferring format from file extension."""
        file_path = Path(file_path)
        if file_path.suffix == ".parquet":
            trajectory = pd.read_parquet(file_path, engine="pyarrow").to_dict(orient="records")

            # Load static info from JSON
            static_info_path = file_path.parent / "static_info.json"
            assert static_info_path.exists(), f"Static info file not found: {static_info_path}"
            with open(static_info_path, "r") as f:
                static_info = json.load(f)
        elif file_path.suffix == ".pkl":
            with open(file_path, "rb") as f:
                data = pickle.load(f)
                trajectory = data["states"]
                static_info = data["static_info"]
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return trajectory, static_info

    def set_track(self, track_name):
        logger.info(f"Setting track {track_name}")
        self.track_config = self.tracks_config[track_name]
        self.track_length = self.track_config["TrackLength"]
        self.track_file = os.path.join(self.tracks_path, self.track_config["track_file"])
        self.ref_lap_file = os.path.join(self.tracks_path, self.track_config["ref_lap_file"])
        self.track_grid_file = os.path.join(self.tracks_path, self.track_config["track_grid_file"])

    def set_eval_mode(self):
        self.max_laps_number = self.config.eval_number_of_laps
        self.use_ac_out_of_track = True