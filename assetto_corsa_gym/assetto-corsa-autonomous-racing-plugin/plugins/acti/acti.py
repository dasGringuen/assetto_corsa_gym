# ========================================================================================================
# Assetto Corsa Telemetry Interface Trigger Control v1.1.2
# - written by Latch Dimitrov - Dec 2017
# - contact: latch(DOT)dimitrov(DOT)00(AT)gmail(DOT)com
# Designed as an in-game trigger control for the Asseto Corsa Telemetry Interface (ACTI) program
# The ACTI package can be downloaded at: [http://www.racedepartment.com/downloads/acti-assetto-corsa-telemetry-interface.3948/]
# ========================================================================================================

import os
import sys
import platform
if platform.architecture()[0] == "64bit":
    sys.path.insert(0, "apps/python/acti/stdlib64")
else:
    sys.path.insert(0, "apps/python/acti/stdlib")
os.environ['PATH'] = os.environ['PATH'] + ";."
import ac
import acsys
import configparser
import locale
import re
import socket
import struct
import subprocess
import sim_info_acti
import time

locale.setlocale(locale.LC_ALL, '')

class Cacti:
    # Window Objects
    mainWindow=0
    settingsWindow=0

    # Labels
    path_label_cntrl=0
    ip_label_cntrl=[0,0,0]

    # Edit boxes
    path_box_cntrl=0
    ip_box_cntrl=[0,0,0]

    # Checkboxes
    auto_launch_chk_cntrl=0
    auto_trigger_chk_cntrl=0

    # (Mini) Trigger control buttons
    save_but_cntrl=0
    load_but_cntrl=0
    settings_but_cntrl=0
    trig_connect_but_cntrl=0
    trig_disconnect_but_cntrl=0
    launch_but_cntrl=0
    fsplice_but_cntrl=0

    # Status icon
    trig_conn_stat_icon_cntrl=0

    # Status box control
    status_box_cntrl=0

    # Window Object Values
    status_box_lines_list=[]
    auto_launch_chk_val=0
    auto_trigger_chk_val=0

    # Comm
    is_using_local_acti=False
    trig_socket=0
    udp2_socket=0
    udp2_dataflow_ip=["", "", ""]
    SOCKET_TIMEOUT=3.0
    ACTI_TRIG_PORT=27150
    ACTI_UDP2_PORT=27151
    TRIG_CONNECT_REQ=5500
    TRIG_DISCONNECT_REQ=5501
    TRIG_KILL_REQ=5502
    TRIG_FSPLICE_REQ=5503
    TRIG_IS_SUBPROC_MSG=5510
    TRIG_ACK=5550
    TRIG_NACK=5551
    TRIG_STATUS_ERROR=-1
    TRIG_STATUS_REFUSED=0
    TRIG_STATUS_ACCEPTED=1

    # Misc
    VERSION="v1.1.2"
    MAX_STATUS_BOX_LINES=15
    text_encoding=""
    text_encoding_override=""
    is_settings_window_visible=False
    init_complete=False
    ac_status_verified=False

    # AC_STATUS
    AC_OFF=0
    AC_REPLAY=1
    AC_LIVE=2
    AC_PAUSE=3

    # AC_SESSION_TYPE
    AC_UNKNOWN=-1
    AC_PRACTICE=0
    AC_QUALIFY=1
    AC_RACE=2
    AC_HOTLAP=3
    AC_TIME_ATTACK=4
    AC_DRIFT=5
    AC_DRAG=6

    #Timers
    flasher_period=0.0
    flasher_running_time=0.0
    flasher_count=0
    flasher_pri_light="apps/python/acti/res/yellow_status_icon.png"
    flasher_sec_light="apps/python/acti/res/yellow_status_icon.png"

    # Logging
    log_level = 1
    def log(self, log_message, indent_level):
        if self.log_level > 1:
            # Status Box
            self.status_box_lines_list.append("        "*indent_level + ">>> " + log_message + "\r\n")
            if len(self.status_box_lines_list) > self.MAX_STATUS_BOX_LINES:
                self.status_box_lines_list.pop(0)
            temp_string = ""
            for line in self.status_box_lines_list:
                temp_string = temp_string + line
            ac.setText(self.status_box_cntrl, temp_string)
            # Console
            ac.console("ACTI: " + log_message)
            pass
        elif self.log_level > 0:
            # Status Box
            self.status_box_lines_list.append("        "*indent_level + ">>> " + log_message + "\r\n")
            if len(self.status_box_lines_list) > self.MAX_STATUS_BOX_LINES:
                self.status_box_lines_list.pop(0)
            temp_string = ""
            for line in self.status_box_lines_list:
                temp_string = temp_string + line
            ac.setText(self.status_box_cntrl, temp_string)

# The acti object
acti = Cacti()

# Try to get the proper text encoding
acti.text_encoding = locale.getpreferredencoding()

def acMain(ac_version):
    global acti

    if platform.architecture()[0] == "64bit":
        acti.log("Starting ACTI Trigger Control %s (64-bit)..." % (acti.VERSION), 0)
    else:
        acti.log("Starting ACTI Trigger Control %s (32-bit)..." % (acti.VERSION), 0)

    # Window Assembly ======================================================================================
    acti.mainWindow = ac.newApp("ACTI Trigger Control")
    ac.setIconPosition(acti.mainWindow, 0, -10000)
    acti.settingsWindow = ac.newApp("ACTI Trigger Control Settings")
    ac.setIconPosition(acti.settingsWindow, 0, -10000)

    # Main Window
    ac.setSize(acti.mainWindow, 179, 61)
    ac.setTitle(acti.mainWindow, "")
    ac.setBackgroundTexture(acti.mainWindow, "apps/python/acti/res/main_background.png")

    # Settings Window
    ac.setSize(acti.settingsWindow, 600, 500)
    ac.setTitle(acti.settingsWindow, "Assetto Corsa Telemetry Interface Trigger Control Settings")

    # Labels
    acti.path_label_cntrl = ac.addLabel(acti.settingsWindow,"Full System Path to Local acti.exe")
    ac.setPosition(acti.path_label_cntrl, 10, 60)

    acti.ip_label_cntrl[0] = ac.addLabel(acti.settingsWindow,"Trigger 0 IP Address")
    ac.setPosition(acti.ip_label_cntrl[0], 10, 110)

    acti.ip_label_cntrl[1] = ac.addLabel(acti.settingsWindow,"Trigger 1 IP Address")
    ac.setPosition(acti.ip_label_cntrl[1], 220, 110)

    acti.ip_label_cntrl[2] = ac.addLabel(acti.settingsWindow,"Trigger 2 IP Address")
    ac.setPosition(acti.ip_label_cntrl[2], 430, 110)

    # Input Boxes
    acti.path_box_cntrl = ac.addTextInput(acti.settingsWindow, "path_box_cntrl")
    ac.setSize(acti.path_box_cntrl, 580, 22)
    ac.setPosition(acti.path_box_cntrl, 10, 80)
    ac.setFontAlignment(acti.path_box_cntrl, "center")

    acti.ip_box_cntrl[0] = ac.addTextInput(acti.settingsWindow, "ip_box_cntrl0")
    ac.setSize(acti.ip_box_cntrl[0], 160, 22)
    ac.setPosition(acti.ip_box_cntrl[0], 10, 130)
    ac.setFontAlignment(acti.ip_box_cntrl[0], "center")

    acti.ip_box_cntrl[1] = ac.addTextInput(acti.settingsWindow, "ip1_box_cntrl1")
    ac.setSize(acti.ip_box_cntrl[1], 160, 22)
    ac.setPosition(acti.ip_box_cntrl[1], 220, 130)
    ac.setFontAlignment(acti.ip_box_cntrl[1], "center")

    acti.ip_box_cntrl[2] = ac.addTextInput(acti.settingsWindow, "ip2_box_cntrl2")
    ac.setSize(acti.ip_box_cntrl[2], 160, 22)
    ac.setPosition(acti.ip_box_cntrl[2], 430, 130)
    ac.setFontAlignment(acti.ip_box_cntrl[2], "center")

    # Checkboxes
    acti.auto_launch_chk_cntrl = ac.addCheckBox(acti.settingsWindow, "Auto Launch Enabled")
    ac.setSize(acti.auto_launch_chk_cntrl, 22, 22)
    ac.setPosition(acti.auto_launch_chk_cntrl, 184, 170)

    acti.auto_trigger_chk_cntrl = ac.addCheckBox(acti.settingsWindow, "Auto Connect Enabled")
    ac.setSize(acti.auto_trigger_chk_cntrl, 22, 22)
    ac.setPosition(acti.auto_trigger_chk_cntrl, 394, 170)

    # Buttons
    acti.save_but_cntrl = ac.addButton(acti.settingsWindow, "Save Settings")
    ac.setSize(acti.save_but_cntrl, 140, 22)
    ac.setPosition(acti.save_but_cntrl, 300, 40)

    acti.load_but_cntrl = ac.addButton(acti.settingsWindow, "Load Settings")
    ac.setSize(acti.load_but_cntrl, 140, 22)
    ac.setPosition(acti.load_but_cntrl, 450, 40)

    acti.settings_but_cntrl = ac.addLabel(acti.mainWindow, "")
    ac.setSize(acti.settings_but_cntrl, 24, 24)
    ac.setPosition(acti.settings_but_cntrl, 4, 18)
    ac.setBackgroundTexture(acti.settings_but_cntrl, "apps/python/acti/res/settings_icon.png")

    acti.trig_connect_but_cntrl = ac.addLabel(acti.mainWindow, "")
    ac.setSize(acti.trig_connect_but_cntrl, 24, 24)
    ac.setPosition(acti.trig_connect_but_cntrl, 31, 18)
    ac.setBackgroundTexture(acti.trig_connect_but_cntrl, "apps/python/acti/res/connect_icon.png")

    acti.trig_disconnect_but_cntrl = ac.addLabel(acti.mainWindow, "")
    ac.setSize(acti.trig_disconnect_but_cntrl, 24, 24)
    ac.setPosition(acti.trig_disconnect_but_cntrl, 97, 18)
    ac.setBackgroundTexture(acti.trig_disconnect_but_cntrl, "apps/python/acti/res/disconnect_icon.png")

    acti.launch_but_cntrl = ac.addLabel(acti.mainWindow, "")
    ac.setSize(acti.launch_but_cntrl, 24, 24)
    ac.setPosition(acti.launch_but_cntrl, 124, 18)
    ac.setBackgroundTexture(acti.launch_but_cntrl, "apps/python/acti/res/launch_icon.png")

    acti.fsplice_but_cntrl = ac.addLabel(acti.mainWindow, "")
    ac.setSize(acti.fsplice_but_cntrl, 24, 24)
    ac.setPosition(acti.fsplice_but_cntrl, 151, 18)
    ac.setBackgroundTexture(acti.fsplice_but_cntrl, "apps/python/acti/res/fsplice_icon.png")

    # Icons
    acti.trig_conn_stat_icon_cntrl = ac.addLabel(acti.mainWindow, "")
    ac.setSize(acti.trig_conn_stat_icon_cntrl, 32, 32)
    ac.setPosition(acti.trig_conn_stat_icon_cntrl, 60, 14)
    ac.setBackgroundTexture(acti.trig_conn_stat_icon_cntrl, "apps/python/acti/res/yellow_status_icon.png")

    # Status Box
    acti.status_box_cntrl = ac.addTextBox(acti.settingsWindow, "status_box_cntrl")
    ac.setSize(acti.status_box_cntrl, 580, 285)
    ac.setPosition(acti.status_box_cntrl, 10, 205)
    ac.setFontSize(acti.status_box_cntrl, 15)
    # ======================================================================================================

    # Callbacks ============================================================================================
    ac.addOnCheckBoxChanged(acti.auto_launch_chk_cntrl, onAutoLaunchChkChange)
    ac.addOnCheckBoxChanged(acti.auto_trigger_chk_cntrl, onAutoTriggerChkChange)
    ac.addOnClickedListener(acti.save_but_cntrl, onSave)
    ac.addOnClickedListener(acti.load_but_cntrl, onLoad)
    ac.addOnClickedListener(acti.settings_but_cntrl, onSettings)
    ac.addOnClickedListener(acti.trig_connect_but_cntrl, onTriggerConnect)
    ac.addOnClickedListener(acti.trig_disconnect_but_cntrl, onTriggerDisconnect)
    ac.addOnClickedListener(acti.launch_but_cntrl, onLaunchACTI)
    ac.addOnClickedListener(acti.fsplice_but_cntrl, onFSPLICE)
    ac.addOnAppActivatedListener(acti.settingsWindow, onSettingsActivated)
    ac.addOnAppDismissedListener(acti.settingsWindow, onSettingsDismissed)
    # ======================================================================================================

    acti.log("ACTI Trigger Control Initialized.", 1)

    # Load Settings
    onLoad(0, 0);

    # Launch ACTI
    if acti.auto_launch_chk_val:
        onLaunchACTI(0, 0)

    # Set up UDP2
    acti.log("Setting Up UDP2...", 1)
    try:
        acti.udp2_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        acti.udp2_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        acti.udp2_socket.settimeout(acti.SOCKET_TIMEOUT)
        acti.log("UDP2 Successfully Set Up.", 2)
    except Exception as e:
        acti.log("UDP2 ERROR. type=%s" % (type(e)), 2)
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)

    acti.init_complete = True

    return "acti"

def acUpdate(deltaT):
    global acti

    # Background manipulation
    ac.setBackgroundOpacity(acti.mainWindow, 0.0)
    ac.drawBorder(acti.mainWindow, 0)
    ac.setBackgroundOpacity(acti.settingsWindow, 1.0)
    ac.drawBorder(acti.settingsWindow, 1)

    # Timers
    if acti.flasher_count > 0:
        acti.flasher_running_time = acti.flasher_running_time - deltaT
        if acti.flasher_running_time <= 0.0:
            if acti.flasher_count % 2:
                ac.setBackgroundTexture(acti.trig_conn_stat_icon_cntrl, acti.flasher_pri_light)
            else:
                ac.setBackgroundTexture(acti.trig_conn_stat_icon_cntrl, acti.flasher_sec_light)
            acti.flasher_running_time = acti.flasher_period
            acti.flasher_count = acti.flasher_count - 1

    # Service UDP2
    try:
        sim_info_obj = sim_info_acti.SimInfo()
        ACTI_CarInfo = ""

        PackingString = "<"; PackingList = []
        # XXXXX "Python" Channels XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        PackingString += "l"; PackingList.append(ac.getCarState(0, acsys.CS.LapTime))

        PackingString += "l"; PackingList.append(int(sim_info_obj.graphics.lastSectorTime))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.performanceMeter))

        PackingString += "l"; PackingList.append(int(sim_info_obj.graphics.status))

        PackingString += "l"; PackingList.append(int(sim_info_obj.graphics.session))

        TempNum = sim_info_obj.graphics.sessionTimeLeft
        if TempNum == float("Inf"):
            PackingString += "l"; PackingList.append(int(0))
        else:
            PackingString += "l"; PackingList.append(int(TempNum))

        PackingString += "l"; PackingList.append(int(sim_info_obj.graphics.position))

        PackingString += "l"; PackingList.append(int(sim_info_obj.graphics.flags))

        PackingString += "l"; PackingList.append(int(sim_info_obj.static.penaltiesEnabled))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.airDensity))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.airTemp))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.roadTemp))

        PackingString += "f"; PackingList.append(float(sim_info_obj.graphics.surfaceGrip))

        PackingString += "f"; PackingList.append(float(sim_info_obj.graphics.windSpeed))

        PackingString += "f"; PackingList.append(float(sim_info_obj.graphics.windDirection))

        TempString = sim_info_obj.static._acVersion
        for i in range(14):
            if i < len(TempString):
                PackingString += "c"; PackingList.append(TempString[i].encode("ascii"))
                PackingString += "c"; PackingList.append("\0".encode("ascii"))
            else:
                PackingString += "c"; PackingList.append("\0".encode("ascii"))
                PackingString += "c"; PackingList.append("\0".encode("ascii"))

        TempString = sim_info_obj.graphics.tyreCompound
        for i in range(32):
            if i < len(TempString):
                PackingString += "c"; PackingList.append(TempString[i].encode("ascii"))
                PackingString += "c"; PackingList.append("\0".encode("ascii"))
            else:
                PackingString += "c"; PackingList.append("\0".encode("ascii"))
                PackingString += "c"; PackingList.append("\0".encode("ascii"))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.ballast))

        PackingString += "l"; PackingList.append(ac.getCarState(0, acsys.CS.Gear)-1)

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.DriveTrainSpeed))

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.TurboBoost))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.fuel))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.engineBrake))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.brakeBias))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.kersCharge))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.kersInput))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.drs))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.ersRecoveryLevel))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.ersPowerLevel))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.ersHeatCharging))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.ersIsCharging))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.kersCurrentKJ))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.drsAvailable))

        PackingString += "l"; PackingList.append(ac.getCarState(0, acsys.CS.LapInvalidated))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.numberOfTyresOut))

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.SuspensionTravel)[0])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.SuspensionTravel)[1])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.SuspensionTravel)[2])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.SuspensionTravel)[3])

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.RideHeight)[0])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.RideHeight)[1])

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.Caster))

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.ToeInDeg, 0))
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.ToeInDeg, 1))
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.ToeInDeg, 2))
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.ToeInDeg, 3))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.pitch))

        PackingString += "f"; PackingList.append(float(sim_info_obj.physics.roll))

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.LocalAngularVelocity)[0])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.LocalAngularVelocity)[1])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.LocalAngularVelocity)[2])

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.LocalVelocity)[0])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.LocalVelocity)[1])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.LocalVelocity)[2])

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)[0])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)[1])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)[2])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)[3])

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.DynamicPressure)[0])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.DynamicPressure)[1])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.DynamicPressure)[2])
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.DynamicPressure)[3])

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreWear))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreWear))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreWear))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreWear))[3])

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.brakeTemp))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.brakeTemp))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.brakeTemp))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.brakeTemp))[3])

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempI))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempI))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempI))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempI))[3])

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempM))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempM))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempM))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempM))[3])

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempO))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempO))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempO))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.tyreTempO))[3])

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.carDamage))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.carDamage))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.carDamage))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.carDamage))[3])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.physics.carDamage))[4])

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.maxTorque))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.maxPower))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.maxTurboBoost))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.maxRpm))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.maxFuel))

        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.static.suspensionMaxTravel))[0])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.static.suspensionMaxTravel))[1])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.static.suspensionMaxTravel))[2])
        PackingString += "f"; PackingList.append(list(map(float, sim_info_obj.static.suspensionMaxTravel))[3])

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.kersMaxJ))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.ersMaxJ))

        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.Aero, acsys.AERO.CD))
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.Aero, acsys.AERO.CL_Front))
        PackingString += "f"; PackingList.append(ac.getCarState(0, acsys.CS.Aero, acsys.AERO.CL_Rear))

        PackingString += "l"; PackingList.append(int(sim_info_obj.physics.autoShifterOn))

        PackingString += "l"; PackingList.append(int(sim_info_obj.graphics.idealLineOn))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.aidFuelRate))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.aidTireRate))

        #PackingString += "f"; PackingList.append(float(sim_info_obj.static.aidMechanicalDamage))
        PackingString += "f"; PackingList.append(float(ac.getCarState(0, acsys.CS.LastFF)))

        PackingString += "l"; PackingList.append(int(sim_info_obj.static.aidAllowTyreBlankets))

        PackingString += "f"; PackingList.append(float(sim_info_obj.static.aidStability))

        PackingString += "l"; PackingList.append(int(sim_info_obj.static.aidAutoClutch))

        PackingString += "l"; PackingList.append(int(sim_info_obj.static.aidAutoBlip))

        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        # AC_STATUS checking and Trigger Connect
        if (acti.ac_status_verified == False) and acti.init_complete:
            ac_status = int(sim_info_obj.graphics.status)
            if (ac_status != acti.AC_OFF) and (ac_status != acti.AC_PAUSE):
                acti.ac_status_verified = True
                if (ac_status == acti.AC_LIVE) and acti.auto_trigger_chk_val:
                    onTriggerConnect(0, 0)

        sim_info_obj.close()
        ACTI_CarInfo = struct.pack(PackingString, *PackingList)

        for iHost in range(3):
            if acti.udp2_dataflow_ip[iHost] != "":
                acti.udp2_socket.sendto(ACTI_CarInfo, (acti.udp2_dataflow_ip[iHost], acti.ACTI_UDP2_PORT))
    except Exception as e:
        acti.log("UDP2 ERROR. type=%s" % ((e)), 2)
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)

def acShutdown(*args):
    global acti
    acti.udp2_socket.close()

def onAutoLaunchChkChange(chk_name, chk_value):
    global acti
    acti.auto_launch_chk_val = chk_value

def onAutoTriggerChkChange(chk_name, chk_value):
    global acti
    acti.auto_trigger_chk_val = chk_value

def onSave(v1, v2):
    global acti
    config = configparser.SafeConfigParser()
    try:
        config.add_section("acti_config")
        config.set("acti_config", "local_acti_full_path", ac.getText(acti.path_box_cntrl))
        config.set("acti_config", "trigger_ip0_address", ac.getText(acti.ip_box_cntrl[0]))
        config.set("acti_config", "trigger_ip1_address", ac.getText(acti.ip_box_cntrl[1]))
        config.set("acti_config", "trigger_ip2_address", ac.getText(acti.ip_box_cntrl[2]))
        config.set("acti_config", "local_acti_auto_launch", str(acti.auto_launch_chk_val))
        config.set("acti_config", "auto_trigger", str(acti.auto_trigger_chk_val))
        config.set("acti_config", "auto_trigger", str(acti.auto_trigger_chk_val))
        config.set("acti_config", "text_encoding_override", acti.text_encoding_override)
        with open("apps/python/acti/config.ini", "w") as config_file:
            config.write(config_file)
        acti.log("Settings Successfully Saved.", 1)
    except Exception as e:
        acti.log("Config ERROR. type=%s" % (type(e)), 1)

def onLoad(v1, v2):
    global acti
    config = configparser.SafeConfigParser()
    try:
        config.read("apps/python/acti/config.ini")
        ac.setText(acti.path_box_cntrl, config.get("acti_config", "local_acti_full_path"))
        ac.setText(acti.ip_box_cntrl[0], config.get("acti_config", "trigger_ip0_address"))
        ac.setText(acti.ip_box_cntrl[1], config.get("acti_config", "trigger_ip1_address"))
        ac.setText(acti.ip_box_cntrl[2], config.get("acti_config", "trigger_ip2_address"))
        acti.auto_launch_chk_val = config.getint("acti_config", "local_acti_auto_launch")
        ac.setValue(acti.auto_launch_chk_cntrl, acti.auto_launch_chk_val)
        acti.auto_trigger_chk_val = config.getint("acti_config", "auto_trigger")
        ac.setValue(acti.auto_trigger_chk_cntrl, acti.auto_trigger_chk_val)
        acti.text_encoding_override = config.get("acti_config", "text_encoding_override")
        if acti.text_encoding_override != "":
            acti.text_encoding = acti.text_encoding_override
        acti.log("Settings Successfully Loaded.", 1)
    except Exception as e:
        acti.log("Config ERROR. type=%s" % (type(e)), 1)

def onSettings(v1, v2):
    global acti

    if acti.is_settings_window_visible == False:
        ac.setVisible(acti.settingsWindow, 1)
        acti.is_settings_window_visible = True
    else:
        ac.setVisible(acti.settingsWindow, 0)
        acti.is_settings_window_visible = False

def onTriggerConnect(v1, v2):
    global acti

    TriggerRetCodes = []

    for iHost in range(3):
        acti.udp2_dataflow_ip[iHost] = ""
        if ac.getText(acti.ip_box_cntrl[iHost]) != "":
            acti.log("Attempting Trigger %d Connect..." % (iHost), 1)
            CurrentTriggerRetCode = trigger(ac.getText(acti.ip_box_cntrl[iHost]), acti.TRIG_CONNECT_REQ, 2)
            if CurrentTriggerRetCode == acti.TRIG_STATUS_ACCEPTED:
                acti.udp2_dataflow_ip[iHost] = ac.getText(acti.ip_box_cntrl[iHost])
            TriggerRetCodes.append(CurrentTriggerRetCode)

    if acti.TRIG_STATUS_ERROR in TriggerRetCodes:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
    elif acti.TRIG_STATUS_REFUSED in TriggerRetCodes:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
    else:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/green_status_icon.png", acti.flasher_pri_light)

def onTriggerDisconnect(v1, v2):
    global acti

    TriggerRetCodes = []

    for iHost in range(3):
        acti.udp2_dataflow_ip[iHost] = ""
        if ac.getText(acti.ip_box_cntrl[iHost]) != "":
            acti.log("Attempting Trigger %d Disconnect..." % (iHost), 1)
            TriggerRetCodes.append( trigger(ac.getText(acti.ip_box_cntrl[iHost]), acti.TRIG_DISCONNECT_REQ, 2) )

    if acti.TRIG_STATUS_ERROR in TriggerRetCodes:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
    elif acti.TRIG_STATUS_REFUSED in TriggerRetCodes:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
    else:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/red_status_icon.png", acti.flasher_pri_light)

def onLaunchACTI(v1, v2):
    global acti

    try:
        acti.log("Attempting Local ACTI Launch... System Text Encoding = %s" % (acti.text_encoding), 1)
        acti_running = False
        Popen_object = subprocess.Popen(["tasklist", "/FI", "STATUS eq RUNNING", "/FI", "WINDOWTITLE eq Assetto Corsa Telemetry Interface"], shell=True, stdout=subprocess.PIPE)
        if re.search("acti.exe", Popen_object.communicate()[0].decode(acti.text_encoding)):
            acti_running = True
        if acti_running:
            acti.log("Local ACTI Already Running.", 2)
        else:
            subprocess.call(["start", "/MIN", "", os.path.normpath(ac.getText(acti.path_box_cntrl))], shell=True)
            time.sleep(1.0)
            Popen_object = subprocess.Popen(["tasklist", "/FI", "STATUS eq RUNNING", "/FI", "WINDOWTITLE eq Assetto Corsa Telemetry Interface"], shell=True, stdout=subprocess.PIPE)
            if re.search("acti.exe", Popen_object.communicate()[0].decode(acti.text_encoding)):
                acti_running = True
            if acti_running:
                acti.log("Local ACTI Launched Successfully. Triggering Local Initialization...", 2)
                TriggerRetCode = trigger("localhost", acti.TRIG_IS_SUBPROC_MSG, 3)
                if TriggerRetCode == acti.TRIG_STATUS_ACCEPTED:
                    acti.is_using_local_acti = True
                else:
                    set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
            else:
                acti.log("Local ACTI Launch FAIL.", 2)
    except Exception as e:
        acti.log("Local ACTI Launch ERROR. type=%s" % (type(e)), 2)

def onFSPLICE(v1, v2):
    global acti

    TriggerRetCodes = []

    for iHost in range(3):
        if ac.getText(acti.ip_box_cntrl[iHost]) != "":
            acti.log("Attempting Trigger %d FSPLICE..." % (iHost), 1)
            TriggerRetCodes.append( trigger(ac.getText(acti.ip_box_cntrl[iHost]), acti.TRIG_FSPLICE_REQ, 2) )

    if acti.TRIG_STATUS_ERROR in TriggerRetCodes:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
    elif acti.TRIG_STATUS_REFUSED in TriggerRetCodes:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/yellow_status_icon.png", acti.flasher_pri_light)
    else:
        set_flasher(0.2, 0.2, 5, "apps/python/acti/res/green_status_icon.png", acti.flasher_pri_light)

def onSettingsActivated(val):
    global acti
    acti.is_settings_window_visible = True

def onSettingsDismissed(val):
    global acti
    acti.is_settings_window_visible = False

def trigger(HostIP, MsgCode, LogIndentLevel):
    global acti

    ret_value = acti.TRIG_STATUS_ERROR

    try:
        acti.trig_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        acti.trig_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        acti.trig_socket.settimeout(acti.SOCKET_TIMEOUT)
        acti.trig_socket.connect((HostIP, acti.ACTI_TRIG_PORT))

        long_var = struct.pack("<l", MsgCode)
        acti.trig_socket.sendall(long_var)
        in_buff = acti.trig_socket.recv(4)
        rec_code = struct.unpack("<l", in_buff)[0]

        if rec_code == acti.TRIG_ACK:
            acti.log("Trigger Accepted.", LogIndentLevel)
            ret_value = acti.TRIG_STATUS_ACCEPTED
        elif rec_code == acti.TRIG_NACK:
            acti.log("Trigger Refused.", LogIndentLevel)
            ret_value = acti.TRIG_STATUS_REFUSED
        else:
            acti.log("Trigger Handshake FAIL. rec_code=%d" % (rec_code), LogIndentLevel)
            ret_value = acti.TRIG_STATUS_ERROR

        acti.trig_socket.close()
    except Exception as e:
        acti.log("Trigger ERROR. type=%s" % (type(e)), LogIndentLevel)
        acti.trig_socket.close()

    return ret_value

def set_flasher(period, running_time, count, pri, sec):
    global acti

    acti.flasher_period=period
    acti.flasher_running_time=running_time
    acti.flasher_count=count
    acti.flasher_pri_light=pri
    acti.flasher_sec_light=sec

    ac.setBackgroundTexture(acti.trig_conn_stat_icon_cntrl, acti.flasher_sec_light)

