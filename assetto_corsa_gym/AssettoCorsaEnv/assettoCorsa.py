import os
import sys
import numpy as np
import copy
from gym.wrappers.time_limit import TimeLimit

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(script_path, 'assetto_corsa_gym')))

import AssettoCorsaEnv.ac_env as ac_env
from AssettoCorsaEnv.ac_client import Client

import logging
logger = logging.getLogger(__name__)

class ModuleConfig:
    env_name = "AssettoCorsaEnv"

    def __init__(self, config) -> None:
        # deep copy and update
        self.config = copy.deepcopy(config)
        self.config.ego_server_host_name = config.remote_machine_ip
        self.config.opponents_server_host_name = config.remote_machine_ip
        self.config.simulation_management_server_host_name = config.remote_machine_ip

        #
        self.max_episode_steps = config.max_episode_py_time * config.ego_sampling_freq

        this_file_path = os.path.abspath(os.path.dirname(__file__))
        self.ac_configs_path = os.path.join(this_file_path, "../AssettoCorsaConfigs")

    def make_env(self, output_path, ac_configs_path=None):
        if ac_configs_path is None:
            ac_configs_path = self.ac_configs_path
        env = ac_env.AssettoCorsaEnv(self.config, # config
                                    use_relative_actions=self.config.use_relative_actions,
                                    ctrl_rate=self.config.ego_sampling_freq,
                                    track_name=self.config.track, car_name=self.config.car,
                                    ac_configs_path=ac_configs_path,
                                    enable_sensors=self.config.enable_sensors,
                                    max_episode_steps=self.max_episode_steps,
                                    enable_out_of_track_termination=self.config.enable_out_of_track_termination,
                                    output_path=output_path, add_previous_obs_to_state=self.config.add_previous_obs_to_state,
                                    enable_low_speed_termination=self.config.enable_low_speed_termination,
                                    recover_car_on_done=self.config.recover_car_on_done,
                                    )

        #env.set_maneuver(self.task, torch_device)  # BRN, BRN_straight, BRN_sector_1, BRN_C01
        self.max_episode_steps = env.max_episode_steps
        self.env = TimeLimit(env, max_episode_steps=self.max_episode_steps)
        return self.env

    def get_config(self):
        return self.config

def make_client_only(config):
    config = ModuleConfig(config)
    return Client(config.get_config())

def make_ac_env(cfg, work_dir=None, ac_configs_path=None):
    if cfg and cfg.task != "AssettoCorsaEnv":
        # config from TDMPC
        raise ValueError('Unknown task:', cfg.task)
    if work_dir is None:
        work_dir = cfg.work_dir.as_posix()
    config = ModuleConfig(cfg.AssettoCorsa)
    env = config.make_env(output_path=work_dir, ac_configs_path=ac_configs_path)
    return env