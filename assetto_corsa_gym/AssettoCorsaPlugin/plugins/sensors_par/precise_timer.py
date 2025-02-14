import ctypes
from ctypes import wintypes
import time

class PreciseTimer:
    def __init__(self, interval):
        self.interval = int(interval * 1000) # interval to milliseconds
        self.timer_id = None

        #
        self.args = None          # Arguments for the function
        self.kwards = None
        self.function = None

        # Load the winmm library
        self.winmm = ctypes.WinDLL('winmm')

        # Define the callback function type
        self.TIMER_CALLBACK = ctypes.WINFUNCTYPE(None, wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong))

        # Timer callback function
        self.callback = self.TIMER_CALLBACK(self._timer_callback)

    def set_function(self, function, *args, **kwargs):
        self.function = function
        self.kwargs = kwargs
        self.args = args

    def _timer_callback(self, hTimer, uMsg, dwUser, dw1, dw2):
        # Call the function with the stored arguments
        self.function(*self.args, **self.kwargs)

    def start(self):
        resolution = 1  # Resolution in milliseconds
        TIME_PERIODIC = 0x0001  # Periodic timer
        self.timer_id = self.winmm.timeSetEvent(self.interval, resolution, self.callback, None, TIME_PERIODIC)

    def stop(self):
        if self.timer_id is not None:
            self.winmm.timeKillEvent(self.timer_id)
            self.timer_id = None

    def stopped(self):
        return self.timer_id is None