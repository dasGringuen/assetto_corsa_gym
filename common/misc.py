import os
import sys
import json
import pickle
import gym
import numpy as np
import subprocess
import torch
import platform
from typing import Dict, Iterable, Optional, Tuple, Union
import logging
logger = logging.getLogger(__name__)

TORCH_DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

'''
    Store to file
'''
def to_json(d, file):
    assert isinstance(d, dict), 'Type mismatch'
    with open(file, 'w') as fp:
        json.dump(d, fp,  indent=4)

def read_json(file):
    with open(file) as f:
        return json.load(f)

def to_pickle(obj, file, verbose=False):
    if verbose: print('saving to..', file)
    with open(file, 'wb') as f: pickle.dump(obj, f)

def read_pickle(file, verbose=False):
    if verbose: print('loading from..', file)
    with open(file, 'rb') as f:
        return pickle.load(f)

'''
Math
'''
def rmse(a, b):
    return np.sqrt(np.mean((a-b)**2))

#from time import localtime, strftime, time
from datetime import datetime

'''
misc
'''
def get_date_timestemp():
    return datetime.now().strftime('%Y%m%d_%H%M%S.%f')[:-3]

import socket
def get_gethostname():
    return socket.gethostname()

def create_run_path(base_path="output"):
    run_path = base_path + os.sep + datetime.now().strftime('%Y%m%d_%H%M%S.%f')[:-3]
    run_path = os.path.abspath(run_path) + os.sep
    os.makedirs(run_path, exist_ok=True)
    return run_path

'''
log to file
'''
class StdOutLogger(object):
    '''
    Example
        sys.stdout = StdOutLogger()
        print('test StdOutLogger')
    '''
    def __init__(self, file_path='', use_timestmap=True):
        if use_timestmap:
            file_name = datetime.strftime(datetime.now(), '%Y%m%d-%H%M%S') + '.log'  # '20190411-164341.log'
        else:
            file_name = 'log.txt'
        file_name = os.path.join(file_path, file_name)
        self.terminal = sys.stdout
        self.log = open(file_name, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

def run_command(cmd, config_path=None, verbose=True):
    # run command in another directoy
    current_path = os.getcwd()
    if config_path is not None:
      os.chdir(config_path)

    return_code = 0
    try:
        if verbose:
            subprocess.check_call(cmd, stdout=sys.stdout, stderr=subprocess.STDOUT)
        else:
            with open(os.devnull, 'w') as tempf:
                subprocess.check_call(cmd, stdout=tempf, stderr=sys.stdout)
    except subprocess.CalledProcessError as e:
        return_code = e.returncode
        print(e)
    except Exception as e:
        print(e)

    # set the path back again
    os.chdir(current_path)
    return return_code

def get_system_info(print_info: bool = True) -> Tuple[Dict[str, str], str]:
    """
    Retrieve system and python env info for the current system.

    :param print_info: Whether to print or not those infos
    :return: Dictionary summing up the version for each relevant package
        and a formatted string.
    """
    env_info = {
        "OS": f"{platform.platform()} {platform.version()}",
        "Python": platform.python_version(),
        "PyTorch": torch.__version__,
        "GPU Enabled": str(torch.cuda.is_available()),
        "Numpy": np.__version__,
        "Gym": gym.__version__,
    }
    env_info_str = ""
    for key, value in env_info.items():
        env_info_str += f"{key}: {value}\n"
    if print_info:
        logger.info(env_info_str)
    return env_info, env_info_str

def get_git_commit_info(print_info = True):
    branch_name = os.popen("git rev-parse --abbrev-ref HEAD").read().strip("\n")
    commit_date = os.popen("git log -n 1 --date=short").read().strip("\n")
    if print_info:
        logger.info(f"Git info. Branch {branch_name}")
        logger.info(f"{commit_date}")
    return commit_date, branch_name