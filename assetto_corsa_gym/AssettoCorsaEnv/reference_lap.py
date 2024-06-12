import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.interpolate import interp1d
from AssettoCorsaEnv.curvature import curvature_splines

import logging
logger = logging.getLogger(__name__)

def get_yaw(x,  y):
    deriv_x = np.diff(x)
    deriv_z = np.diff(y)
    angle = np.arctan2(deriv_z, deriv_x)
    # do not wrap, we want the angle from -pi to pi
    return angle

def distSegment2Index(rl_dist, l_bound, u_bound):
    return np.where(np.logical_and(rl_dist >= l_bound, rl_dist <= u_bound))

def calculate_distance_from_xy(x, y):
    x_diff = np.diff(x)
    y_diff = np.diff(y)

    dist = np.cumsum(np.hypot(x_diff, y_diff) )
    dist = np.insert(dist, 0, 0)
    return dist

def convert_to_distance(distance, ch, interp_type="linear"):
    """
    Interpolate every channel to make the distance the independent variable

    interp_type: "linear" or cubic (linear x6 faster)
    """
    def monotonic(x):
        dx = np.diff(x)
        #print(np.all(dx >= 0))
        return np.all(dx <= 0) or np.all(dx >= 0), dx

    _, dx = monotonic(distance)

    # check for consecutive equal samples
    # for the interpolation we need a monotonically increasing function
    equal_samples = np.where(dx <= 0)[0]
    if len(equal_samples):
        print("Warning: check for consecutive equal samples. Found ", equal_samples, "samples")
        last_sample = equal_samples[0]# - 1
        print("Will crop from %d samples to %d samples" % (len(distance), last_sample))
    else:
        last_sample = -1

    distance = distance[:last_sample]
    ch = ch[:last_sample]
    tck = {}
    out = {}
    p = distance
    last_dist = distance[-1] + 3 # add 3 meters to the interpolation
    x = np.arange(0, last_dist)
    tck = interp1d(p, ch, kind=interp_type, fill_value="extrapolate")
    return tck(x)

class ReferenceLap:
    """
    Can use any line. Just x,y are needed. Distance, yaw and curvature are calculated
    Optionally curvature could be from file and target_speed

    Warning: the last point of the racing line should precede the first point to avoid discontinuities in the gap.

    racing_line
        array:
            pos,xyz, dist, yaw, curvature

    racing_line_dist
        array
            same but interpolated and cropped so that the distance is monotonically increasing
    """
    file_channels = ["pos_x", "pos_y"]
    target_speed_channel_name = "target_speed"

    # new names (access with .index("pos_x"))
    # channels =      ["position.x", "position.y", "lapDistance", "yaw", "curvature", "target_speed"]
    # channels_dist = ["position.x", "position.y", "lapDistance", "yaw", "curvature", "target_speed"]
    channels =      ["position.x", "position.y", "lapDistance", "yaw", "curvature"]
    channels_dist = ["position.x", "position.y", "lapDistance", "yaw", "curvature"]

    def __init__(self, file_path, use_target_speed):
        logger.info(f"Reference Lap. Loading: {file_path}")
        self.file_path = file_path
        self.df = pd.read_csv(file_path)
        self.df = self.df.reset_index()
        self.use_target_speed = use_target_speed

        try:
            self.ts = self.df[self.file_channels].values
        except KeyError:
            logger.error(f"Channels {self.file_channels} not found.")
            logger.error(f"Channels in racing line file: {self.df.columns}")
            raise

        if self.use_target_speed:
            self.target_speed = self.df[self.target_speed_channel_name].values.reshape(-1,1)
            print(self.target_speed)
            logger.info("Using target speed")
            self.channels.append(self.target_speed_channel_name)
            self.channels_dist.append(self.target_speed_channel_name)

        # calculate distance channels from x,y coordinates
        self.distance_ch_time = calculate_distance_from_xy(self.ts[:,0], self.ts[:,1])
        self.ts = np.concatenate([self.ts, self.distance_ch_time.reshape(-1,1)], axis=1)

        # calculate angle_y from x,y coordinates
        # calculate the yaw, fl gives a yaw wrapped to pi
        yaw = get_yaw(self.ts[:,0], self.ts[:,1])
        yaw = np.insert(yaw, 0, yaw[0]).reshape(-1,1)
        self.ts = np.concatenate([self.ts, yaw], axis=1)

        # calculate curvature
        # If the curvature is present in the racing line use it else calculate it
        if "curvature" in self.df.columns:
            logger.info("Using curvature from racing line file")
            curvatures = self.df["curvature"].values.reshape(-1,1)
        else:
            logger.info("Calculating curvature")
            curvatures = curvature_splines( self.ts[:,0],  self.ts[:,1] )
            curvatures = curvatures.reshape(-1,1)
        self.ts = np.concatenate([self.ts, curvatures], axis=1)

        if self.use_target_speed:
            self.ts = np.concatenate([self.ts, self.target_speed], axis=1)

        # interpolate to distance
        td = []
        for _, ch in enumerate(self.channels_dist):
            idx = self.channels.index(ch)
            td.append( convert_to_distance(self.distance_ch_time, self.ts[:,idx]) )
        self.td = np.array( td ).T
        self.distance_ch_dist = self.td[:,2]

    def get_racing_line_time(self):
        return self.ts[:, 0:2]

    def get_racing_line_dist(self):
        return self.td[:, 0:2]

    def get_channel_time(self, channel_name):
        return self.ts[:,self.channels.index(channel_name)].reshape(-1,1)

    def get_channel_dist(self, channel_name):
        return self.td[:,self.channels.index(channel_name)].reshape(-1,1)

    """
    Curvature look ahead
    """
    def distSegment2Index(self, rl_dist, l_bound, u_bound):
        return np.where((rl_dist >= l_bound) & (rl_dist <= u_bound))[0]

    def getLADVector(self, rl_dist, dist, LA_dist, vector_size, channel):
        """
            Get a vector (len vector_size) of a channel at max LA_dist

            rl_dist: time series with the distance channel interpolated and projected to distance
            dist: current distance of the car
            LA_dist: how far to look ahead [m]
            vector_size: downsample the result to this value
            channel: distance interpolated channel
            returns: vector of vector_size with the channel interpolated by distance

        """
        rl_dist = rl_dist.copy()
        patch = 0
        track_len = rl_dist[-1]

        if ((dist - track_len) > 50):
            print("## look ahead was out of range!!! Will return a Zero Vector", dist, track_len)
            assert ((dist - track_len) > 50), "distance was more than 50 meters bigger than the track len dist %f track_len %f" \
                                               % (dist, track_len)

        start = dist
        end = dist + LA_dist
        segment = self.distSegment2Index(rl_dist, start, end)

        if end > track_len:
            patch = end - track_len
            segment = np.concatenate( [segment, self.distSegment2Index(rl_dist, 0, patch)] )

        vector = channel[segment]
        vector = vector[0::len(vector) // vector_size]
        vector = vector[0:vector_size]
        return vector, segment, patch

    def get_curvature_segment(self, dist, LA_dist, vector_size):
        """
        Get single value curvature:
            dist: starting distance in the racing line
            LA_dist: lookahed starting from dist
            vector_size: downsampled signal size
        """
        curv_index = self.channels_dist.index("curvature")
        vector, segment, patch = self.getLADVector(self.distance_ch_dist, dist, LA_dist, vector_size, self.td[:, curv_index])
        return vector

    def get_target_speed_segment(self, dist, LA_dist, vector_size):
        """
        Get single value curvature:
            dist: starting distance in the racing line
            LA_dist: lookahed starting from dist
            vector_size: downsampled signal size
        """
        assert self.use_target_speed, "target speed not used"

        target_speed_index = self.channels_dist.index("target_speed")
        vector, segment, patch = self.getLADVector(self.distance_ch_dist, dist, LA_dist, vector_size, self.td[:, target_speed_index])
        return vector

    def get_target_speed_value(self, dist):
        """
        Get single value of the target speed
        """
        assert self.use_target_speed, "target speed not enabled"

        target_speed_index = self.channels_dist.index("target_speed")
        vector, segment, patch = self.getLADVector(self.distance_ch_dist, dist, 200., 1, self.td[:, target_speed_index])
        return vector[0]

    def get_yaw(self, dist):
        """
        Get single value curvature
        """
        curv_index = self.channels_dist.index("yaw")
        vector, segment, patch = self.getLADVector(self.distance_ch, dist, 200., 1, self.racing_line_dist[:,curv_index])
        return vector[0]

    def get_curvature(self, dist):
        """
        Get single value curvature
        """
        curv_index = self.channels_dist.index("curvature")
        vector, segment, patch = self.getLADVector(self.distance_ch, dist, 200., 1, self.racing_line_dist[:,curv_index])
        return vector

    def cropped_racing_line(self, start, segment_len, vector_len):
        pos_x_idx = self.channels_dist.index("pos_x")
        pos_y_idx = self.channels_dist.index("pos_y")
        racing_line_cropped_x, _, _ = self.getLADVector(self.distance_ch, start,
                                                        segment_len, vector_len, self.racing_line_dist[:,pos_x_idx])
        racing_line_cropped_y, _, _ = self.getLADVector(self.distance_ch, start,
                                                        segment_len, vector_len, self.racing_line_dist[:,pos_y_idx])
        return np.vstack([ racing_line_cropped_x, racing_line_cropped_y ]).T