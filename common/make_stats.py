
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob as glob
import sys
import os
import time
from scipy.ndimage import gaussian_filter
from tqdm import tqdm
import mpld3
#mpld3.enable_notebook()
import pickle
import datetime
import socket
import time
import traceback
import yaml
from pathlib import Path
from AssettoCorsaEnv.motec_loader import MotecLoader

import logging
logger = logging.getLogger(__name__)

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Format of the log messages
    datefmt='%Y-%m-%d %H:%M:%S',  # Format of the timestamp
)
logger = logging.getLogger(__name__)


sys.path.append(os.path.abspath(os.path.join('../assetto_corsa_gym')))
from AssettoCorsaEnv.data_loader import *


dataset_path = Path(r"." + os.sep)
paths = get_path_for_track_car(dataset_path=dataset_path, file='paths.yml', track="ks_barcelona-layout_gp", car="ks_mazda_miata")

dataset_path = Path(r"." + os.sep)
get_all_paths_in_file("paths.yml", dataset_path, filter_track="ks_barcelona-layout_gp", filter_car="ks_mazda_miata")


data_dir = r"C:\Users\aremonda\Dropbox\zshared_temp\assetto_corsa_rl\data_sets"
dataset_path = Path(data_dir + os.sep)


load_paths = get_all_paths_in_file(dataset_path=dataset_path, file='paths.yml', filter_tags={"type": "human", "data_type": "motec"})




load_path = load_paths[4]

assert Path(load_path).exists()
load_path


laps_path = glob.glob(f'{load_path}/*.ld')

for f in laps_path:
    print(os.path.basename(f))
    lap = MotecLoader(f, ac_fps=50, target_freq=25, ignore_fps_missmatch=True)



def lap_times_list(df):
    laps_info = []
    for i in list(set(df["LapCount"])):
        if i == 0: # discard out lap
            continue
        l = df[df["LapCount"] == i]
        t = l["lastLapTime"].values[-1]
        #print(i, data_loader.seconds_to_mm_ss_mmm(t), t)
        r = {"LapCount": i, "LapTime": t.round(4), "LapTimeStr": seconds_to_mm_ss_mmm(t),
             "speed_max": l["speed"].max() * 3.6, "speed_avg": l["speed"].mean() * 3.6,
             "steps": len(l)
            }
        laps_info.append(r.copy())
    laps_info = pd.DataFrame(laps_info, index=None).round(3)
    best_lap = laps_info['LapTime'].idxmin()+1

    stint_stats = {
        "name": load_path.split("/")[-3],
        "car": load_path.split("/")[-4],
        "track": load_path.split("/")[-5],
        "path": load_path,
        "best_lap": best_lap,
        "best_lap_time": laps_info.loc[best_lap-1]["LapTime"],
        "best_lap_time_str": laps_info.loc[best_lap-1]["LapTimeStr"],
        "number_of_laps": len(laps_info),
        "speed_max": laps_info["speed_max"].max(),
        "speed_mean": laps_info["speed_avg"].max(),
        "steps": laps_info.steps.sum(),
    }

    return laps_info, stint_stats

laps_info, stint_stats = lap_times_list(lap.ts)
laps_info.to_csv(f"{load_path}/laps_info.csv")
laps_info, stint_stats


all_users = []
for load_path in load_paths:
    laps_path = glob.glob(f'{load_path}/*.ld')

    assert len(laps_path), load_path

    for i, f in enumerate(laps_path):
        logger.info(f)
        lap = MotecLoader(f, ac_fps=50, target_freq=25, ignore_fps_missmatch=True)
        laps_info, stint_stats = lap_times_list(lap.ts)
        laps_info.to_csv(f"{load_path}/laps_info.csv")
        all_users.append(stint_stats)

stint_stats = pd.DataFrame(all_users)
stint_stats.to_excel("all_stats.xlsx")
stint_stats["number_of_laps"].sum()


# car: # monza ks_barcelona-layout_gp ks_red_bull_ring-layout_gp
# tracka:  dallara_f317, ks_mazda_miata, bmw_z4_gt3

stint_stats[(stint_stats["car"] == "ks_mazda_miata") & (stint_stats["track"] == "ks_barcelona-layout_gp")]


stint_stats[(stint_stats["car"] == "dallara_f317") & (stint_stats["track"] == "ks_barcelona-layout_gp")]


stint_stats[(stint_stats["car"] == "bmw_z4_gt3") & (stint_stats["track"] == "ks_barcelona-layout_gp")]





# car: # monza ks_barcelona-layout_gp ks_red_bull_ring-layout_gp
# tracka:  dallara_f317, ks_mazda_miata, bmw_z4_gt3

stint_stats[(stint_stats["car"] == "ks_mazda_miata") & (stint_stats["track"] == "ks_barcelona-layout_gp")]





