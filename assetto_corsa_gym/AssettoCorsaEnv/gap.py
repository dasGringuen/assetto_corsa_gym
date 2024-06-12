import numpy as np
import torch
from .gap_torch import get_gap as get_gap_torch
from .gap_cpu import get_gap as get_gap_cpu

def get_gap(points, racing_line, calculate_distance=False, cum_distance_in_racing_line=None):
    if isinstance(points, np.ndarray):
        return get_gap_cpu(points, racing_line, calculate_distance, cum_distance_in_racing_line )
    elif isinstance(points, torch.Tensor):
        return get_gap_torch(points, racing_line, calculate_distance, cum_distance_in_racing_line)

