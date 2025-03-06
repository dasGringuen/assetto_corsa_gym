        # Original controls_rate_limit (in deg/s scaled per time step)
        self.controls_rate_limit = np.array([[-1500, 1500],   # steering: deg/s
                                              [-1200/100, 1200/100],  # pedal: (falling edge)
                                              [-1200/100, 1200/100],  # brake: (release/press)
                                             ]) * (1/self.ctrl_rate)

        # Define physical and simulator parameters for each channel.
        # For steering: max physical angle is 240° and the corresponding normalized value is 0.52.
        self.max_steer_deg = 240.0
        self.norm_steer_at_max = 0.52
        # Conversion factor (deg per normalized unit) for steering.
        self.steering_scale_factor = self.max_steer_deg / self.norm_steer_at_max
        # For pedal and brake: full range is already [0,1].
        # Create a per-channel scale factor vector.
        self.controls_scale_factor = np.array([self.steering_scale_factor, 1.0, 1.0])
        # Adjust the rate-limit vector per channel (element-wise division along the second axis)
        self.adjusted_controls_rate_limit = self.controls_rate_limit / self.controls_scale_factor[:, np.newaxis]

        # Now, set the absolute limits for the simulator.
        # For steering, use the normalized value corresponding to max steering.
        self.controls_min_values = np.array([-self.norm_steer_at_max, -1.0, -1.0])
        self.controls_max_values = np.array([ self.norm_steer_at_max,  1.0,  1.0])

        # actions space is always -1 to 1 for most algorithms
        self.action_dim = 3
        self.action_space = Box(low=np.array([-1.0, -1.0, -1.0]), high=np.array([1.0, 1.0, 1.0]))


    def preprocess_actions(self, actions, current_actions):
        if self.use_relative_actions:
            # Fully vectorized update: scale each action by the adjusted per-channel rate limit.
            new_actions = current_actions + actions * self.adjusted_controls_rate_limit[:, 1]
        else:
            new_actions = actions
        return np.clip(new_actions, self.controls_min_values, self.controls_max_values)


    def inverse_preprocess_actions(self, prev_abs_actions, current_abs_actions):
        if self.use_relative_actions:
            # Use the adjusted rate limit's upper bound for each channel.
            max_delta = self.adjusted_controls_rate_limit[:, 1]
            actions = (current_abs_actions - prev_abs_actions) / max_delta
            return np.clip(actions, -1.0, 1.0)
        else:
            return np.clip(current_abs_actions, self.controls_min_values, self.controls_max_values)
