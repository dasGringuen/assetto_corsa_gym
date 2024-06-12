import numpy as np
import pandas as pd
from itertools import groupby
from AssettoCorsaEnv.motec_ldparser import ldData
import logging
logger = logging.getLogger(__name__)
from scipy.signal import savgol_filter
from tqdm import tqdm
import glob
import pickle
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

def to_pickle(file, obj, verbose=False):
    if verbose: print('saving to..', file)
    with open(file, 'wb') as f:
        pickle.dump(obj, f)

def get_yaw(x,  y):
    deriv_x = np.diff(x)
    deriv_z = np.diff(y)
    angle = np.arctan2(deriv_z, deriv_x)
    # do not wrap, we want the angle from -pi to pi
    return angle

def get_smooth_yaw(x, y):

    # Assuming `x` and `y` are your car's position data arrays
    x_smooth = savgol_filter(x, window_length=50, polyorder=6)  # Adjust window_length and polyorder as necessary
    y_smooth = savgol_filter(y, window_length=50, polyorder=6)

    # Calculate yaw from smoothed positions
    yaw = np.arctan2(np.diff(y_smooth), np.diff(x_smooth))
    return yaw

class MotecLoader:
    keep_channels = [
        "speed",  # from 'ground speed'
        "world_position_x",  # from 'car coord y'
        "world_position_y",  # from '-car coord x'
        "RPM",  # from 'engine rpm'
        "LapCount",  # from 'session lap count'
        "NormalizedSplinePosition",  # from 'car pos norm'
        "numberOfTyresOut",  # from 'num tires off track'
        "accelX",  # from 'cg accel lateral'
        "accelY",  # from 'cg accel longitudinal'
        "SlipAngle_fl",  # assumption from 'tire slip angle fl'
        "SlipAngle_fr",
        "SlipAngle_rl",
        "SlipAngle_rr",
        "tyre_slip_ratio_fl",
        "tyre_slip_ratio_fr",
        "tyre_slip_ratio_rl",
        "tyre_slip_ratio_rr",
        "angular_velocity_y",  # from '-chassis yaw rate' / 180 * np.pi
        "actualGear",  # from 'gear' + 1
        "local_velocity_x",  # assumed direct rename from 'chassis velocity x'
        "local_velocity_y",  # from '-chassis velocity y'
        "accStatus",
        "steerAngle",
        "brakeStatus",
        "yaw",
    ]

    def __init__(self, file, ac_fps=50, target_freq=25, use_mech_damage_as_lastFF_channel=True,
                 ignore_fps_missmatch=False):
        self.file = file
        self.ts = None
        self.ac_fps = ac_fps
        self.target_freq = target_freq
        self.ignore_fps_missmatch = ignore_fps_missmatch
        self.use_mech_damage_as_lastFF_channel = use_mech_damage_as_lastFF_channel
        self.down_sample = self.ac_fps // self.target_freq
        logger.info(f"Assetto Corsa FPS: {self.ac_fps}, Target Frequency: {self.target_freq}, Downsample: {self.down_sample}")

        if self.use_mech_damage_as_lastFF_channel:
            logger.info("Using 'aid mech damage' as lastFF (force feedback) channel")

        self.load_lap(file)

    def load_lap(self, file):
        self.lap = ldData.fromfile(file)
        logger.info(f"Loaded {file}")
        logger.debug(self.lap.head)
        logger.debug(list(map(str, self.lap)))

        self.vehicleid = self.lap.head.vehicleid
        self.track = self.lap.head.venue

        # create plots for all channels with the same frequency
        for i, g in groupby(self.lap.channs, lambda x:x.freq):
            df = pd.DataFrame({i.name.lower(): i.data for i in g})
            logger.info(f"Group frequency {i}")
            #assert i == 100, "TODO check this. 100Hz is expected"

        # Renaming ground speed to speed and dividing by 3.6
        df['ground speed'] = df['ground speed'] / 3.6
        df.rename(columns={'ground speed': 'speed'}, inplace=True)

        # Directly renaming other columns as per the mapping provided
        rename_columns = {
            'car coord y': 'world_position_x',
            'car coord x': 'world_position_y',  # Temporarily rename to transform next
            'engine rpm': 'RPM',
            'session lap count': 'LapCount',
            'car pos norm': 'NormalizedSplinePosition',
            'num tires off track': 'numberOfTyresOut',
            'cg accel lateral': 'accelX',
            'cg accel longitudinal': 'accelY',
            'tire slip angle fl': 'SlipAngle_fl',
            'tire slip angle fr': 'SlipAngle_fr',
            'tire slip angle rl': 'SlipAngle_rl',
            'tire slip angle rr': 'SlipAngle_rr',
            'tire slip ratio fl': 'tyre_slip_ratio_fl',
            'tire slip ratio fr': 'tyre_slip_ratio_fr',
            'tire slip ratio rl': 'tyre_slip_ratio_rl',
            'tire slip ratio rr': 'tyre_slip_ratio_rr',
            'chassis velocity x': 'local_velocity_x',
            'steering angle': 'steerAngle',
            'throttle pos': 'accStatus',        # Accelerator pos
            'brake pos': 'brakeStatus',         # Brake pos
            'last lap time': 'lastLapTime',
        }
        df["currentTime"] = df["lap time"] # to keep the original
        df.rename(columns=rename_columns, inplace=True)

        # Transformations that require calculation
        df['world_position_y'] = -df['world_position_y']  # Inverting sign
        df['chassis yaw rate'] = -df['chassis yaw rate'] / 180 * np.pi
        df.rename(columns={'chassis yaw rate': 'angular_velocity_y'}, inplace=True)

        df['gear'] = df['gear'] + 1
        df.rename(columns={'gear': 'actualGear'}, inplace=True)

        # Assuming 'chassis velocity y' needs inversion and rename
        df['chassis velocity y'] = -df['chassis velocity y']
        df.rename(columns={'chassis velocity y': 'local_velocity_y'}, inplace=True)

        df['tyre_slip_ratio_fl'] = df['tyre_slip_ratio_fl'] / 100.
        df['tyre_slip_ratio_fr'] = df['tyre_slip_ratio_fr'] / 100.
        df['tyre_slip_ratio_rl'] = df['tyre_slip_ratio_rl'] / 100.
        df['tyre_slip_ratio_rr'] = df['tyre_slip_ratio_rr'] / 100.

        #
        df['brakeStatus'] = df['brakeStatus'] / 100.
        df['accStatus'] = df['accStatus'] / 100.

        #yaw = get_yaw(df.world_position_x.values, df.world_position_y.values)
        yaw = get_smooth_yaw(df.world_position_x.values, df.world_position_y.values)

        #df['yaw'] = np.concatenate(([yaw[0]], yaw))
        #df['yaw'] = np.insert(yaw, -1, yaw[-1])#.reshape(-1,1)
        df['yaw'] = np.insert(yaw, 0, yaw[0])#.reshape(-1,1)
        # heading = np.arctan2(df.local_velocity_y.values, df.local_velocity_x.values)

        df['done'] = np.zeros(len(df))

        if self.use_mech_damage_as_lastFF_channel:
            df['LastFF'] = df['aid mech damage'] / 100.

        # Remove consecutive repeated values
        df = df[df['currentTime'].diff() != 0]

        deltas = np.diff( df.currentTime.values )
        deltas = deltas[deltas > 0.] # remove end of the track discontinuity

        df["fps"] = df["raw data sample rate"]
        read_fps = int( df["fps"].mean() )
        read_freq = 1. / deltas.mean()
        logger.info(f"Average fps in telemetry: {read_fps}")
        logger.info(f"Average filtered fps: {read_freq}")

        if not (self.ac_fps - 2 <= read_freq <= self.ac_fps + 2):
            logger.warning(f"Assetto Corsa telemetry frequency is not as expected. Got: {read_freq} and should be {self.ac_fps}")
            if not self.ignore_fps_missmatch:
                raise ValueError(f"Assetto Corsa telemetry frequency is not as expected")

        # downsample
        df = df.iloc[::self.down_sample]
        df.reset_index(drop=True, inplace=True)
        self.ts = df.copy()


def convert_motec_to_state_pickle(motec_file, env, ac_fps=50, target_freq=25, ignore_fps_missmatch=False):
    lap = MotecLoader(motec_file, ac_fps=ac_fps, target_freq=target_freq, ignore_fps_missmatch=ignore_fps_missmatch)

    def expand_state_wrapper(row):
        state, info = env.expand_state(row.to_dict())
        return state  # Assuming you only need to collect states

    # Applying the function and collecting results
    states = lap.ts.apply(expand_state_wrapper, axis=1).tolist()
    output_file = Path(motec_file).with_suffix('.pkl')
    to_pickle(output_file, {'states': states, 'static_info': ""})
    logger.info(f"Exported to {output_file}")
    return states

def convert_all_in_path(path, env, ac_fps=50, target_freq=25, ignore_fps_missmatch=False):
    for f in glob.glob(path + "/*.ld"):
        convert_motec_to_state_pickle(f, env=env, ac_fps=ac_fps, target_freq=target_freq, ignore_fps_missmatch=ignore_fps_missmatch)