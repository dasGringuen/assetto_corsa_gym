from abc import ABC, abstractmethod
import os
import numpy as np
import torch


class Algorithm(ABC):

    @abstractmethod
    def __init__(self, state_dim, action_dim, device, gamma=0.99, nstep=1,
                 log_interval=10, seed=0):
        # Set seed.
        torch.manual_seed(seed)
        np.random.seed(seed)
        # torch.backends.cudnn.deterministic = True  # It harms a performance.
        # torch.backends.cudnn.benchmark = False  # It harms a performance.

        self._learning_steps = 0
        self._state_dim = state_dim
        self._action_dim = action_dim
        self._device = device
        self._gamma = gamma
        self._nstep = nstep
        self._discount = gamma ** nstep
        self._log_interval = log_interval

    @abstractmethod
    def explore(self, state):
        pass

    @abstractmethod
    def exploit(self, state):
        pass

    @abstractmethod
    def update_target_networks(self):
        pass

    @abstractmethod
    def update_online_networks(self, batch, writer):
        pass

    @abstractmethod
    def save_models(self, save_dir):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    @property
    def gamma(self):
        return self._gamma

    @property
    def nstep(self):
        return self._nstep
