Run AC with Proton

use protonQT to add Proton 9-2 to AC

after a long installation for proton related prefix, fail for the first time, start again and succeeds. 

in sensor_par/vjoy_linux.py
for which input event in /dev/input is used, need to find out by
1. first install evtest with sudo apt-get evtest, and cat /proc/bus/input/devices, find out which input device corresponds to virtual xbox360
2. second look over the sudo evtest /dev/input/event11, find out its configuration and revise in vjoy_linux line 74-79
3. scaled_steering value range should be mapped accordingly (value maybe depend on the OS )

Move sensorpar to the plugin location (same)

follow video to install AC context manager https://www.youtube.com/watch?v=8qy_RQr8LbM

need to update to the latest version of custom shaded patch, otherwise there will be INIReader::cache error: see https://github.com/ac-custom-shaders-patch/acc-extension-config/issues/493

comment out win32event, win32con in ego_server currently, currently not support for image

change python path in alternative_python.py, comment out alternative_python

remember to run virtual xbox command

in AC, choose vjoy and then xbox360 game pad

other useful resources: https://steamcommunity.com/sharedfiles/filedetails/?id=2828364666