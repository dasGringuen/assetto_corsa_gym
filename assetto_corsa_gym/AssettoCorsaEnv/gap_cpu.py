"""
Racing Line Gap Calculation
This code needs some optimization
"""

import numpy as np
import torch

def length(v):
    return np.sqrt(np.sum(np.square(v), axis=1) )

def vector(b,e):
    return e - b

def distance(p0, p1):
    return length(vector(p0, p1))

def add(v,w):
    return v + w

def unit(v):
    mag = length(v)
    assert all( mag > 0. ), "segment cannot be of len zero. First and last segment of the racing line should not overlap"
    # https://stackoverflow.com/questions/19602187/numpy-divide-each-row-by-a-vector-element
    return (v.T / mag).T

def get_segment_to_point_dist(start, end, points):
    # Convert the line segment to a vector
    line_vec = vector(start, end)
    # Create a vector connecting start to pnt
    pnt_vec = vector(start, points)
    # Find the length of the line vector
    line_len = length(line_vec)
    #  Convert line_vec to a unit vector
    line_unitvec = unit(line_vec)
    # Scale pnt_vec by line_len
    s = 1.0 / line_len
    pnt_vec_scaled = (pnt_vec.T * s).T

    # Get the dot product of line_unitvec and pnt_vec_scaled
    # Use row wise dot product
    t = np.sum(line_unitvec*pnt_vec_scaled, axis=1)

    # Ensure t is in the range 0 to 1.
    t = np.clip(t, 0, 1)
    # Use t to get the nearest location on the line to the end
    #    of vector pnt_vec_scaled ('nearest').
    # scale line_vec to t
    nearest =  (line_vec.T * t).T
    # Calculate the distance from nearest to pnt_vec_scaled.
    dist = distance(nearest, pnt_vec)
    # Translate nearest back to the start/end line.
    nearest = add(nearest, start)

    cross_product = np.cross(line_vec, pnt_vec)
    sign = np.sign(cross_product) # if zero is orthogonal, otherwise it represents the side of the projection
    projected_segment_len = line_len * t
    return dist, nearest, t, sign, projected_segment_len  # (N,) (N,2) (N,)

def get_gap(points, racing_line, calculate_distance=False, cum_distance_in_racing_line=None):
    '''
    source: From https://newbedev.com/find-the-shortest-distance-between-a-point-and-line-segments-not-line

    points are shape (N, 2) -> 2 dimensions (x,y)
                'VehiclePositionX', 'VehiclePositionY'
    racing_line (M, 2) -> M number of points to consider, 2 dimensions  (x,y)
                'VehiclePositionX', 'VehiclePositionY', 'VehicleHeading'

    calculate_distance: when true enables the calculation of the distance projected onto the racing line.
    cum_distance_in_racing_line: cumulative distance of each segment in the racing line.
                                 Needed to calculate calculate_distance

    returns gap to the racing line
    '''
    xcoords =  points[:,0].reshape(1,-1).transpose() - racing_line[:,0]
    ycoords =  points[:,1].reshape(1,-1).transpose() - racing_line[:,1]

    # dist shape: N, M. distance of each point to each point in the racing line
    dist = np.sqrt( np.square(xcoords) + np.square(ycoords) )

    # get index in the racing line to the minimum euclidian distance for each point
    rl_point = np.argmin(dist, axis=1)#.reshape(1,-1)   # shpae (9,)

    # if closest point is in position 0 change to 1. Needed to calculate the segment later
    rl_point[np.where(rl_point > (len(racing_line) - 2)  )] = len(racing_line) -2

    # calculate the points and dist for the two segment that connect the nearest point
    start = racing_line[rl_point-1]
    end = racing_line[rl_point+0]

    dist_s0, points_s0, t_s0, angle_s0, projection_len_s0 = get_segment_to_point_dist(start, end, points)

    start = racing_line[rl_point+0]
    end = racing_line[rl_point+1]
    dist_s1, points_s1, t_s1, angle_s1, projection_len_s1 = get_segment_to_point_dist(start, end, points)

    # start with zero
    closest_points = points_s1.copy()
    if calculate_distance:
        closest_segments = projection_len_s1.copy()
        cum_dist_to_rl_point = cum_distance_in_racing_line[rl_point].copy()

    #closest_points = np.zeros_like(points_s1)

    # # write s1 first
    # ok_idx_s1 = np.where((t_s1 > 0.0) & (t_s1 < 1.0))
    # closest_points[ok_idx_s1] = points_s1[ok_idx_s1]
    # closest_points

    # overwrite with s0 (means that s0 has priority)
    ok_idx_s0 = np.where((t_s0 > 0.0) & (t_s0 < 1.0))
    closest_points[ok_idx_s0] = points_s0[ok_idx_s0]
    rl_point[ok_idx_s0] = rl_point[ok_idx_s0] - 1  # we consider the previous point to the racing line for all s0 segments

    # if we are in segment 0 then use the previous point in the racing line.
    # Otherwise we keep the pivot point (rl_point+0)
    if calculate_distance:
        closest_segments[ok_idx_s0] = projection_len_s0[ok_idx_s0]
        cum_dist_to_rl_point[ok_idx_s0] = cum_distance_in_racing_line[rl_point[ok_idx_s0]]

    # ----
    # without this block from 238us to 196 µs
    # overlapping case
    # get index to overlapping entries
    ok_idx_s0_and_s1 = np.where((t_s0 > 0.0) & (t_s0 < 1.0) & (t_s1 > 0.0) & (t_s1 < 1.0))

    # get which segment has a lower distance (N,)
    dist_min = np.argmin( [dist_s0 , dist_s1 ], axis=0)

    # overwrite cloestpoint with overlapping indexes
    closest_points[ok_idx_s0_and_s1] = (points_s0[ok_idx_s0_and_s1].T * ((dist_min == 0) * 1.0)[ok_idx_s0_and_s1]).T + \
                                       (points_s1[ok_idx_s0_and_s1].T * ((dist_min == 1) * 1.0)[ok_idx_s0_and_s1]).T

    gap = distance(closest_points, points)
    gap = gap * angle_s0 * (-1)
    if calculate_distance:
        dist = cum_dist_to_rl_point + closest_segments
        return gap, rl_point, closest_points, dist
    else:
        return gap, rl_point, closest_points, None
