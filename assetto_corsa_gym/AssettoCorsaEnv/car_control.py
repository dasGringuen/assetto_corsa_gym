from AssettoCorsaEnv.vjoy import vJoy

import logging
logger = logging.getLogger(__name__)

SCALE = 16384

class Controls(object):
    def __init__(self):
        self.onButtons = 0
        #self.vj = vj
        self.vj = vJoy()

        self.vj.open()

        # internal state
        self.steer = 1.0        # [0, 2]
        self.acc = 0.0          # [0, 1]
        self.brake = 0.0        # [0, 1]
        self.enable_clutch = 0
        self.clutch = 0.
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

    def set_controls(self, steer, acc, brake, enable_clutch=False, clutch=-1, enable_gear_shift=False, shift_up=False, shift_down=False):
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

            # # set gear
            # gear = info.physics.gear - 1
            # print("current gear: %d | required gear is %d " % (gear, data.data))
            # if gear > data.data:
            #     setJoy(self.steer, self.acc, self.brake, 0x00000002, SCALE)
            # elif gear < data.data:
            #     setJoy(self.steer, self.acc, self.brake, 0x00000001, SCALE)

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
        if onButtons != 0:
            joystickPosition = self.vj.generateJoystickPosition(wAxisX= xPos, wAxisY=yPos, wAxisZ=zPos, lButtons=onButtons)
            self.vj.update(joystickPosition)

        joystickPosition = self.vj.generateJoystickPosition(wAxisX= xPos, wAxisY=yPos, wAxisZ=zPos)
        self.vj.update(joystickPosition)

    def gearUp(self):
        """ For testing """

        #press
        self.setJoy(1 ,0.3, 0, 0x00000001, 16384)

        #release
        self.setJoy(1 ,0.3, 0, 0, 16384)
