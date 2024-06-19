from scipy.interpolate import interp1d
import xml.etree.ElementTree as ET

import pandas as pd
import numpy as np

from AssettoCorsaEnv.track_occupancy_grid import TrackOccupancyGrid

import logging
logger = logging.getLogger(__name__)

def interpolate_signal(original, output_len):
    d = np.linspace(0, len(original), num=len(original), endpoint=True)

    new_d = np.linspace(0, len(original), num=output_len, endpoint=True)
    return interp1d(d, original, kind='cubic', fill_value="extrapolate")(new_d)

from numba import jit
from numba.np.extensions import cross2d

@jit(nopython=True)
def in_quadrilateral(boxes, points):
    '''
    Finds whether a point is inside a quadrilateral

    If the point is inside the area of the quadrilateral (seen as two triangles)
    should be the same (or near the same) as the sum of the areas of the four rectangles that
    make each vertex and the point.
    '''
    # (N, 4, 2) = boxes.shape
    # (M, 2) = points.shape
    (A, D, B, C) = np.split(boxes, 4, axis=1)  # (N, 1, 2)
    M = points[None, ...]  # (M, 2)

    AM = (M - A)  # (N, M, 2)
    CM = (M - C)  # (N, M, 2)

    AB = (B - A)  # (N, 1, 2)
    AD = (D - A)  # (N, 1, 2)

    CB = (B - C)  # (N, 1, 2)
    CD = (D - C)  # (N, 1, 2)

    area = (np.abs(cross2d(AM, AB)) + np.abs(cross2d(AM, AD)) +
            np.abs(cross2d(CM, CB)) + np.abs(cross2d(CM, CD)))
    total_area = np.abs(cross2d(AB[0], AD[0])) + np.abs(cross2d(CB[0], CD[0]))

    in_box = area <= total_area + 1e-9

    # Manual implementation of np.any across a specific axis. To make it compatible with numba
    def any_in_box(in_box):
        result = np.zeros(in_box.shape[1], dtype=np.bool_)
        for i in range(in_box.shape[1]):
            for j in range(in_box.shape[0]):
                if in_box[j, i]:
                    result[i] = True
                    break
        return result

    return any_in_box(in_box)

def get_yaw(x, y):
    deriv_x, deriv_y = np.diff(x), np.diff(y)
    return np.arctan2(deriv_y, deriv_x)


class Track:
    def __init__(self, track_file_path, track_grid_file=None, torch_device=None, downsample_segments=10):
        self.file_path = track_file_path
        self.track_grid_file = track_grid_file
        self.downsample_segments = downsample_segments
        if track_grid_file is not None:
            self.track_occupancy_grid = TrackOccupancyGrid(track_grid_file=self.track_grid_file, torch_device=torch_device)

        self.track = pd.read_csv(track_file_path)

        self.left_border_x = self.custom_downsample(self.track.left_border_x.values)
        self.left_border_y = self.custom_downsample(self.track.left_border_y.values)
        self.right_border_x = self.custom_downsample(self.track.right_border_x.values)
        self.right_border_y = self.custom_downsample(self.track.right_border_y.values)

        # self.middle_x = self.track.middle_x.values
        # self.middle_y = self.track.middle_y.values
        # self.middle_z = self.track.middle_z.values

        # self.middle_yaw = self.track.middle_yaw.values

        self.num_segments = self.right_border_x.shape[0]

        # interleave right and left border of the track -> N*2, 2
        #self.stack_middle = np.vstack([self.middle_x, self.middle_y]).T # stack all rb x,y -> N,2
        self.stack_rb = np.vstack([self.right_border_x, self.right_border_y]).T # stack all rb x,y -> N,2
        self.stack_lb = np.vstack([self.left_border_x, self.left_border_y]).T   # stack all lb x,y -> N,2
        self.lr_track = np.stack([self.stack_rb, self.stack_lb], axis=1).reshape(-1,2)

        logger.info(f"Track loaded from: {track_file_path} Found {self.num_segments * downsample_segments} "
                    f"segments downsampled by {downsample_segments}= {self.num_segments} segments")

    def custom_downsample(self, array):
        downsampled = array[::self.downsample_segments]
        # Ensure the last element is included
        if downsampled[-1] != array[-1]:
            downsampled = np.append(downsampled, array[-1])
        return downsampled

    def is_point_in_segment(self, point, segment_idx):
        '''
        true if the point is inside the segment
        '''
        corners = np.array( [self.lr_track[0 + segment_idx * 2 : 4 + segment_idx * 2]] )
        found = in_quadrilateral(corners, point)
        return found[0]

    def get_segment_id(self, point):
        '''
        returns the segment id. -1 if it was not found (out of track)
        '''
        for segment_idx in range(self.num_segments - 1):
            if self.is_point_in_segment(point, segment_idx):
                return segment_idx
        return -1

    def is_point_in_segments_range(self, point, start_segment, end_segment):
        '''
        Search if a point is inside a certain range from start_segment to end_segment
            start and end can be outside the index and they will be wraped

        return of a found segment, -1 if point was not inside any segment
        '''
        def wrap_index(i):
            return i % (self.num_segments - 1)

        i = wrap_index(start_segment)
        end_segment = wrap_index(end_segment)

        while True:
            i += 1
            i = wrap_index(i)
            if self.is_point_in_segment(point, i):
                return i
            if i == end_segment:
                break
        return -1

    def closest_node(self, point):
        '''
        get closest point of the middle of the track to a point
        '''
        nodes = self.stack_middle
        dist_2 = np.sum((nodes - point)**2, axis=1)
        return np.argmin(dist_2)

    def export(self, file):
        self.track.to_csv(file, index=None)
