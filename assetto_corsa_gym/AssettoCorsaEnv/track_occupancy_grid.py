import numpy as np
import torch
import pickle

class TrackOccupancyGrid:
    """
    Creation of the occupancy grid map
        - Needs left and right border of the track to define quadrilateral segments
        - Track was not interpolated. Depends on the application. Should match the one used
        - Update: now is_inside_grid returns the segment number + 1, a value of zero means out of track
                Depends on how the data was created
    """
    def __init__(self, track_grid_file, torch_device=None):
        self.track_grid_file = track_grid_file
        self.torch_device = torch_device

        track_map = self.read_file()

        self.min_x, self.min_y, self.max_x, self.max_y = track_map['min_x'], track_map['min_y'], \
                                                         track_map['max_x'], track_map['max_y']
        self.cell_size = track_map['cell_size']

        points, x_range, y_range = self.get_grid_points()
        found_base = track_map['grid']
        self.grid_map = found_base.reshape(y_range.shape[0], x_range.shape[0]).T

        # make sure that the corners doesn't have parts of the track (see is_inside_grid)
        assert self.is_inside_grid(np.array([[self.min_x, self.min_y]])) == 0
        assert self.is_inside_grid(np.array([[self.min_x, self.max_y]])) == 0
        assert self.is_inside_grid(np.array([[self.max_x, self.min_y]])) == 0
        assert self.is_inside_grid(np.array([[self.max_x, self.max_y]])) == 0

        # allocate some variables in the GPU
        if self.torch_device:
            self.grid_map_torch = torch.from_numpy(self.grid_map).to(torch_device).float()
            self.min_x_torch = torch.from_numpy(np.asarray(self.min_x)).to(torch_device).float()
            self.min_y_torch = torch.from_numpy(np.asarray(self.min_y)).to(torch_device).float()
            self.max_x_torch = torch.from_numpy(np.asarray(self.max_x)).to(torch_device).float()
            self.max_y_torch = torch.from_numpy(np.asarray(self.max_y)).to(torch_device).float()
            self.cell_size_torch = torch.from_numpy(np.asarray(self.cell_size)).to(torch_device).float()
            self.min_p = torch.tensor( [self.min_x_torch, self.min_y_torch ]).float().to(torch_device)
            self.max_p = torch.tensor( [self.max_x_torch - self.cell_size_torch,
                                   self.max_y_torch - self.cell_size_torch]).float().to(torch_device)

    def is_inside_grid(self, points):
        """
        returns zero if out of track and the segment number + 1 otherwise
        """
        if isinstance(points, np.ndarray):

            # 1) coords to idx
            # clip to bound. This means that out of bound values will be clamped to the borders
            # and detected as out of track. Need this trick to make the parallelization easier.
            points = np.clip(points, [self.min_x, self.min_y],
                                     [self.max_x - self.cell_size,
                                     self.max_y - self.cell_size]
                                    )
            min_p = np.array( [self.min_x, self.min_y ])

            # int ( (p - min) / cell )
            index = (np.round((points - min_p) / self.cell_size)).astype(int)

            # 2) return the map
            return self.grid_map[index[:,0], index[:,1]]
        elif isinstance(points, torch.Tensor):
            #points = torch.clip(points, self.min_p, self.max_p)
            points = torch.max(torch.min(points, self.max_p), self.min_p)  # clip(points, min, max)
            index = (torch.round((points - self.min_p) / self.cell_size_torch)).long()
            return self.grid_map_torch[index[:,0], index[:,1]]

    def get_grid_points(self):
        ''' for debugging '''
        x_range = np.arange(self.min_x, self.max_x, self.cell_size)
        y_range = np.arange(self.min_y, self.max_y, self.cell_size)

        xx, yy = np.meshgrid(x_range, y_range)
        points = np.vstack([xx.ravel(), yy.ravel()]).T
        return points, x_range, y_range

    def read_file(self):
        with open(self.track_grid_file,'rb') as f:
            track_map = pickle.load(f)
        return track_map
