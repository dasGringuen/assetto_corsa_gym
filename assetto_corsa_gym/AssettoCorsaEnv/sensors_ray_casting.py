import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle

import logging
logger = logging.getLogger(__name__)

MAX_RAY_LEN = 200.
N_RAYS = 11  # total rays is this plus one (the one in the middle)

EPSILON = 1e-9
GRID_SIZE = 20  # size of the SpatialHash grid in meters

class SpatialHash:
    def __init__(self, walls, verbose=False):
        self.walls = walls
        self.cell_size = self.get_cell_size()
        self.spatial_hash = self.create_hash()
        if verbose:
            print(f"Ranges: {self.wall_xmin} {self.wall_ymin} {self.wall_xmax} {self.wall_ymax} cell_size: {self.cell_size}")

        # Print the spatial hash
        if verbose:
            for cell_coords, wall_indices in self.spatial_hash.items():
                print(f"Cell {cell_coords} contains wall segments {wall_indices}")

    def get_cell_size(self):
        self.wall_xmin = min( np.min( self.walls[:, 0] ), np.min( self.walls[:, 2] ) )
        self.wall_ymin = min( np.min( self.walls[:, 1] ), np.min( self.walls[:, 3] ) )
        self.wall_xmax = max( np.max( self.walls[:, 0] ), np.max( self.walls[:, 2] ) )
        self.wall_ymax = max( np.max( self.walls[:, 1] ), np.max( self.walls[:, 3] ) )

        max_range = max(self.wall_xmax - self.wall_xmin, self.wall_ymax - self.wall_ymin)
        return round(max_range / GRID_SIZE, 1)

    def create_hash(self):
        spatial_hash = {}

        # Insert the walls into the spatial hash
        for i, wall in enumerate(self.walls):
            xmin = min(wall[0], wall[2])
            ymin = min(wall[1], wall[3])
            xmax = max(wall[0], wall[2])
            ymax = max(wall[1], wall[3])

            for x in np.arange(xmin, xmax + EPSILON, self.cell_size):
                for y in np.arange(ymin, ymax + EPSILON, self.cell_size):
                    cell_coords = (int(x / self.cell_size), int(y / self.cell_size))

                    if cell_coords not in spatial_hash:
                        spatial_hash[cell_coords] = []

                    spatial_hash[cell_coords].append(i)

        logger.info(f"spatial_hash len {len(spatial_hash)}")
        return spatial_hash

    def query(self, rectangle):
        """
        spatial_hash len 918 = 1.5m
        spatial_hash len  35 = 70us
        spatial_hash len   1 = 21us
        """
        xmin = min(rectangle[0], rectangle[2])
        ymin = min(rectangle[1], rectangle[3])
        xmax = max(rectangle[0], rectangle[2])
        ymax = max(rectangle[1], rectangle[3])

        wall_indices = set()

        for x in np.arange(xmin, xmax + EPSILON, self.cell_size):
            for y in np.arange(ymin, ymax + EPSILON, self.cell_size):
                cell_coords = (int(x / self.cell_size), int(y / self.cell_size))
                if cell_coords in self.spatial_hash:
                    wall_indices.update(self.spatial_hash[cell_coords])

        return list(wall_indices)

    def rectangle_from_point(self, point, width):
        half_width = width / 2
        return [point[0] - half_width, point[1] - half_width, point[0] + half_width, point[1] + half_width]

    def rectangle_from_center_point(self, center, width, height):
        half_width = width / 2
        half_height = height / 2
        return [center[0] - half_width, center[1] - half_height, center[0] + half_width, center[1] + half_height]

    def get_filtered_walls_in_rectangle(self, point, rectangle_width):
        rectangle = self.rectangle_from_center_point(point, rectangle_width, rectangle_width)

        # crop to bounds
        rectangle[0] = max(rectangle[0], self.wall_xmin - self.cell_size)
        rectangle[1] = max(rectangle[1], self.wall_ymin - self.cell_size)
        rectangle[2] = min(rectangle[2], self.wall_xmax + self.cell_size)
        rectangle[3] = min(rectangle[3], self.wall_ymax + self.cell_size)

        wall_indices = self.query(rectangle)
        return self.walls[wall_indices], rectangle

    def draw_grid(self):
        # Create the horizontal and vertical line positions
        cell_size = self.cell_size
        x_positions = np.arange(self.wall_xmin, self.wall_xmax + cell_size, cell_size)
        y_positions = np.arange(self.wall_ymin, self.wall_ymax + cell_size, cell_size)

        # Draw the horizontal lines
        for y in y_positions:
            plt.plot([self.wall_xmin, self.wall_xmax], [y, y], color='lightgray')

        # Draw the vertical lines
        for x in x_positions:
            plt.plot([x, x], [self.wall_ymin, self.wall_ymax], color='lightgray')

def convert_sequences_of_points_to_segments(x, y):
    """
    x: shape (n,) -> x coordinates of points
    y: shape (n,) -> y coordinates of points

    return: shape (n-1, 4) -> [(x1, y1, x2, y2), ...]
    """
    return np.vstack((x[:-1], y[:-1], x[1:], y[1:])).T

# Draw functions
def draw_rectangle(rectangle):
    lower_left = (rectangle[0], rectangle[1])
    width = rectangle[2] - rectangle[0]
    height = rectangle[3] - rectangle[1]
    rect = patches.Rectangle(lower_left, width, height, linewidth=1, edgecolor='r', facecolor='none')
    return rect

def ray_casting_vectorized_v2(points, angles, walls, max_distance):
    """
    points: shape (n, 2) -> [(x1, y1), (x2, y2), ...]
    angles: shape (m,) -> [angle1, angle2, ...]
    walls: shape (k, 4) -> [(x1, y1, x2, y2), ...]
    max_distance: float
    """
    walls = np.array(walls, dtype=float)
    x1, y1, x2, y2 = walls.T
    x2_x1 = x2 - x1
    y2_y1 = y2 - y1

    x, y = points.T
    cos_angles = np.cos(angles)[:, None]
    sin_angles = np.sin(angles)[:, None]

    det_A = cos_angles * y2_y1 - sin_angles * x2_x1
    det_A[det_A == 0] = 1e-8  # Set zero elements to a small tolerance value

    valid_indices = np.where(det_A != 0)
    if valid_indices[0].size == 0:
        return points, np.ones(len(points)) * max_distance

    x_x1 = x1 - x[:, None]
    y_y1 = y1 - y[:, None]

    t = (x_x1 * y2_y1 - y_y1 * x2_x1) / det_A
    u = (x_x1 * sin_angles - y_y1 * cos_angles) / det_A

    intersections = np.logical_and(u >= 0, np.logical_and(u <= 1, t >= 0))
    if not intersections.any():
        return points, np.ones(len(points)) * max_distance

    # Set t to inf for rays that do not intersect any wall
    t[~intersections] = max_distance # float('inf')

    min_distance = np.min(t, axis=-1)

    intersections = np.stack([x + cos_angles.squeeze() * min_distance, y + sin_angles.squeeze() * min_distance], axis=-1)

    vector = intersections - points
    vector_lengths = np.linalg.norm(vector, axis=1)
    return intersections, vector_lengths

def make_plots(scene, filtered_walls, points, intersections, x, y, rectangle, number_of_rays, show_cropped=False):
    # Plot the walls
    plt.figure(figsize=(8, 8))
    for wall in scene.walls:
        x1, y1, x2, y2 = wall
        plt.plot([x1, x2], [y1, y2], color='gray')

    for wall in filtered_walls:
        x1, y1, x2, y2 = wall
        plt.plot([x1, x2], [y1, y2], 'k-', color='darkgray')

    rect = draw_rectangle(rectangle)
    scene.draw_grid()

    # Plot the rays
    for i, (point, intersection) in enumerate(zip(points, intersections)):
        if i == int(number_of_rays / 2):
            color = 'blue'
        else:
            color = 'gray'
        plt.plot(*intersection, '.', markersize=2., color="blue")
        plt.plot([point[0], intersection[0]], [point[1], intersection[1]], color)

    plt.gca().add_patch(rect)

    # Plot the starting points of the rays
    plt.plot(points[:, 0], points[:, 1], 'bo', markersize=1)

    plt.gca().set_aspect('equal', adjustable='box')

    if show_cropped:
        plt.xlim(x - 200, x + 200)
        plt.ylim(y - 200, y + 200)

class SensorsRayCasting:
    """ Ray casting sensors implementation using spatial hash """
    def __init__(self, right_border_x, right_border_y, left_border_x, left_border_y, number_of_rays=N_RAYS, verbose=False):
        """
        right_border_x: shape (n,) -> x coordinates of points
        right_border_y: shape (n,) -> y coordinates of points
        left_border_x: shape (n,) -> x coordinates of points
        left_border_y: shape (n,) -> y coordinates of points
        """
        self.number_of_rays = number_of_rays
        right_border = convert_sequences_of_points_to_segments(right_border_x, right_border_y)
        left_border = convert_sequences_of_points_to_segments(left_border_x, left_border_y)

        self.walls = np.vstack((right_border, left_border))

        self.scene = SpatialHash(walls=self.walls, verbose=verbose)

        self.warning_shown = False

    def get_intersections_and_distances_to_wall(self, x, y, angle):
        """
        point: shape (2,) -> (x, y)
        angle: shape (1,) -> angle in radians

        Note: ~155us for 10 rays on a laptop
        """
        # number_of_rays must be odd
        assert self.number_of_rays % 2 != 0, "number of rays must be odd"

        scene = self.scene
        point = np.array([x, y])

        # Create an array of angles covering 360 degrees
        angles = np.linspace(0, np.pi, num=self.number_of_rays, endpoint=True) + angle - np.pi / 2

        # Tile the point to match the size of the angles array
        points = np.tile(point, (len(angles), 1))

        rectangle_width = MAX_RAY_LEN * 2
        filtered_walls, rectangle = scene.get_filtered_walls_in_rectangle(point, rectangle_width)

        if len(angles) * len(filtered_walls) > 2000:
            if not self.warning_shown:
                self.warning_shown = True
                print(f"warning will calculate {len(angles) * len(filtered_walls)} rays. (> 10000 points is too much. 2000 is recommended)")

        intersections, vector_lengths = ray_casting_vectorized_v2(points, angles, filtered_walls, MAX_RAY_LEN)
        return intersections, vector_lengths, filtered_walls, points, rectangle

