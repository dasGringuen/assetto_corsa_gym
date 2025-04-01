import os

if os.name == 'posix':
    from AssettoCorsaEnv.vjoy_linux import vJoy
else:
    from AssettoCorsaEnv.vjoy import vJoy

import logging
logger = logging.getLogger(__name__)

SCALE = 16384

class Controls(object):
    def __init__(self):
        self.onButtons = 0
        self.vj = vJoy()
        self.vj.open()

        # internal state
        self.steer = 1.0        # [0, 2]
        self.acc = 0.0          # [0, 1]
        self.brake = 0.0        # [0, 1]
        self.enable_gear_shift = 0.
        self.shift_up = 0.
        self.shift_down = 0.

        # commands
        self.steer_cmd = 0.0 # [-1,1]
        self.pedal_cmd = 0.0 # [-1,1]
        self.brake_cmd = 0.0 # [-1,1]

        self.ct_12_stop = False

    def close(self):
        self.vj.close()

    def trigger_emergency_stop(self):
        self.ct_12_stop = True
        self.steer= 1.0
        self.acc = 0.0
        self.brake = 0.5
        logger.info("CT12 triggered")
        self.update()

    def set_controls(self, steer, acc, brake, enable_gear_shift=False, shift_up=False, shift_down=False):
        self.steer_cmd = steer
        self.pedal_cmd = acc
        self.brake_cmd = brake

        if not self.ct_12_stop:
            self.steer = self.steer_cmd + 1
            if(self.steer < 0):
                self.steer = 0
            elif(self.steer > 2):
                self.steer = 2

            # Acc
            self.acc = (self.pedal_cmd + 1) / 2
            if(self.acc < 0):
                self.acc = 0
            elif(self.acc > 1):
                self.acc = 1

            # brake
            self.brake = (self.brake_cmd + 1) / 2
            if(self.brake < 0):
                self.brake = 0
            elif(self.brake > 1):
                self.brake = 1

            if enable_gear_shift:
                if shift_up:
                    self.onButtons = 0x00000001  # shift up
                elif shift_down:
                    self.onButtons = 0x00000002
                else:
                    self.onButtons = 0
            else:
                self.onButtons = 0
        self.update()

    def update(self):
        self.setJoy(self.steer, self.acc, self.brake, self.onButtons, SCALE)

    def setJoy(self, valueX, valueY, valueZ, onButtons, scale):
        """
        valueX between 0 and 2
        valueY, valueZ between 0 and 1
        scale between 0 and 16000
        """
        xPos = int(valueX * scale)
        yPos = int(valueY * 2 * scale)
        zPos = int(valueZ * 2 * scale)

        joystickPosition = self.vj.generateJoystickPosition(wAxisX= xPos, wAxisY=yPos, wAxisZ=zPos, lButtons=onButtons)
        self.vj.update(joystickPosition)