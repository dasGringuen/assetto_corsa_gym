
class Config(object):
    def __init__(self):
        self.version = "0.0.1"
        self.sampling_freq = 50  # in Hz  # main tick sampling (FPS of AC)
        self.sampling_time = 1 / self.sampling_freq
        self.ego_server_host_name = "0.0.0.0"
        self.ego_server_port = 2345
        self.ego_sampling_freq = 25 # in Hz # downsampled tick sampling (FPS of ego server)
        self.telemetry_sampling_freq = 0 # in Hz # 0 disables it

        self.opponents_server_host_name = "0.0.0.0"
        self.opponents_server_port = 2346

        self.simulation_management_server_host_name = "0.0.0.0"
        self.simulation_management_server_port = 2347

        self.enable_profiler = False
        self.vjoy_executed_by_server = False

        if self.vjoy_executed_by_server:
            assert self.sampling_freq == 100, "vJoy is executed by the server. The sampling frequency must be 100 Hz to avoid lagging."
        else:
            assert self.sampling_freq == 50, "vJoy is executed by the client. The sampling frequency must be 50 Hz to avoid lagging."

config = Config()