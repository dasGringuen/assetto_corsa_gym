import ctypes
import struct, time
import math

CONST_DLL_VJOY = "C:\\Program Files\\vJoy\\x64\\vJoyInterface.dll"

class vJoy(object):
    def __init__(self, reference=1):
        self.handle = None
        self.dll = ctypes.CDLL(CONST_DLL_VJOY)
        self.reference = reference
        self.acquired = False

    def open(self):
        if self.dll.AcquireVJD(self.reference):
            self.acquired = True
            return True
        return False

    def close(self):
        if self.dll.RelinquishVJD(self.reference):
            self.acquired = False
            return True
        return False

    def generateJoystickPosition(self,
                                 wThrottle=0, wRudder=0, wAileron=0,
                                 wAxisX=0, wAxisY=0, wAxisZ=0,
                                 wAxisXRot=0, wAxisYRot=0, wAxisZRot=0,
                                 wSlider=0, wDial=0, wWheel=0,
                                 wAxisVX=0, wAxisVY=0, wAxisVZ=0,
                                 wAxisVBRX=0, wAxisVBRY=0, wAxisVBRZ=0,
                                 lButtons=0, bHats=0, bHatsEx1=0, bHatsEx2=0, bHatsEx3=0):
        """
        typedef struct _JOYSTICK_POSITION
        {
            BYTE    bDevice; // Index of device. 1-based
            LONG    wThrottle;
            LONG    wRudder;
            LONG    wAileron;
            LONG    wAxisX;
            LONG    wAxisY;
            LONG    wAxisZ;
            LONG    wAxisXRot;
            LONG    wAxisYRot;
            LONG    wAxisZRot;
            LONG    wSlider;
            LONG    wDial;
            LONG    wWheel;
            LONG    wAxisVX;
            LONG    wAxisVY;
            LONG    wAxisVZ;
            LONG    wAxisVBRX;
            LONG    wAxisVBRY;
            LONG    wAxisVBRZ;
            LONG    lButtons;   // 32 buttons: 0x00000001 means button1 is pressed, 0x80000000 -> button32 is pressed
            DWORD   bHats;      // Lower 4 bits: HAT switch or 16-bit of continuous HAT switch
                        DWORD   bHatsEx1;   // 16-bit of continuous HAT switch
                        DWORD   bHatsEx2;   // 16-bit of continuous HAT switch
                        DWORD   bHatsEx3;   // 16-bit of continuous HAT switch
        } JOYSTICK_POSITION, *PJOYSTICK_POSITION;
        """
        joyPosFormat = "BlllllllllllllllllllIIII"
        pos = struct.pack(joyPosFormat, self.reference, wThrottle, wRudder,
                          wAileron, wAxisX, wAxisY, wAxisZ, wAxisXRot, wAxisYRot,
                          wAxisZRot, wSlider, wDial, wWheel, wAxisVX, wAxisVY, wAxisVZ,
                          wAxisVBRX, wAxisVBRY, wAxisVBRZ, lButtons, bHats, bHatsEx1, bHatsEx2, bHatsEx3)
        return pos

    def update(self, joystickPosition):
        if self.dll.UpdateVJD(self.reference, joystickPosition):
            return True
        return False

    # Not working, send buttons one by one
    def sendButtons(self, bState):
        joyPosition = self.generateJoystickPosition(lButtons=bState)
        return self.update(joyPosition)

    def setButton(self, index, state):
        if self.dll.SetBtn(state, self.reference, index):
            return True
        return False

# valueX between 0 and 2
# valueY, valueZ between 0 and 1
# scale between 0 and 16000
def setJoy(valueX, valueY, valueZ, onButtons, scale):
    xPos = int(valueX * scale)
    yPos = int(valueY * 2 * scale)
    zPos = int(valueZ * 2 * scale)
    #yPos = int(valueY * scale)
    #zPos = int(valueZ * scale)
    if onButtons != 0:
        joystickPosition = vj.generateJoystickPosition(wAxisX= xPos, wAxisY=yPos, wAxisZ=zPos, lButtons=onButtons)
        vj.update(joystickPosition)
        time.sleep(0.01)

    joystickPosition = vj.generateJoystickPosition(wAxisX= xPos, wAxisY=yPos, wAxisZ=zPos)
    vj.update(joystickPosition)


# Only for testing
def gearUp():
    #press
    setJoy(1 ,0.3, 0, 0x00000001, 16384)

    #release
    setJoy(1 ,0.3, 0, 0, 16384)
