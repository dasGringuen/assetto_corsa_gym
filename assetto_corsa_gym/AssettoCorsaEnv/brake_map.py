import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

class BrakeMap:
    def __init__(self, x_points, y_points, kind='cubic'):
        self.kind = kind
        self.x_points = x_points
        self.y_points = y_points
        self.initialize(self.x_points, self.y_points, self.kind)

    def initialize(self, x_points, y_points, kind='cubic'):
        self.y_interp_func = interp1d(x_points, y_points, kind=kind, fill_value="extrapolate")

        # Assuming y_points are sorted or the function is mostly monotonic for x(y) interpolation
        self.x_interp_func = interp1d(y_points, x_points, kind=kind, fill_value="extrapolate")

    def get_y(self, x):
        x = np.clip(x, -1, 1)
        y = self.y_interp_func(x)
        return np.clip(y, 0, 1)

    def get_x(self, y):
        y = np.clip(y, 0, 1)
        return self.x_interp_func(y)

    def save(self, filename='brake_map.csv'):
        df = pd.DataFrame({'x_points': self.x_points, 'y_points': self.y_points})
        df.to_csv(filename, index=False)

    @staticmethod
    def load(filename='brake_map.csv'):
        df = pd.read_csv(filename)
        return BrakeMap(df['x_points'].tolist(), df['y_points'].tolist())