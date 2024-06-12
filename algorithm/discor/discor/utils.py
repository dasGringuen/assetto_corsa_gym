from collections import deque
import numpy as np
import torch
from torch import nn


def update_params(optim, loss, retain_graph=False):
    optim.zero_grad()
    loss.backward(retain_graph=retain_graph)
    optim.step()


def disable_gradients(network):
    for param in network.parameters():
        param.requires_grad = False


def _soft_update(target, source, tau):
    target.data.copy_(target.data * (1.0 - tau) + source.data * tau)


def soft_update(target, source, tau):
    assert isinstance(target, nn.Module) or isinstance(target, torch.Tensor)

    if isinstance(target, nn.Module):
        for t, s in zip(target.parameters(), source.parameters()):
            _soft_update(t, s, tau)

    elif isinstance(target, torch.Tensor):
        _soft_update(target, source, tau)

    else:
        raise NotImplementedError


def assert_action(action):
    assert isinstance(action, np.ndarray)
    assert not np.isnan(np.sum(action)), 'Action has a Nan value.'


class RunningMeanStats:

    def __init__(self, n=10):
        assert isinstance(n, int) and n > 0
        self._stats = deque(maxlen=n)

    def append(self, x):
        self._stats.append(x)

    def get(self):
        return np.mean(self._stats)
