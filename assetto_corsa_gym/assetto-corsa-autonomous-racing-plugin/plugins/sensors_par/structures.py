import ac
import acsys
import json
import math
import time
import traceback
import os
import struct
from operator import itemgetter
import sys

sys.path.insert(0, "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\system\\x64\\DLLs")
sys.path.insert(0, "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\system\\x64\\Lib")
from sim_info import info

import logging
logger = logging.getLogger(__name__)

class Car(dict):

    def __init__(self, car_id, send_extra_channels=True):
        self.car_id = car_id
        self["steps"] = 0
        self["timestamp_ac"] = time.perf_counter()
        self.send_extra_channels = send_extra_channels
        self.total_errors_out_of_sync = 0

    def update(self, track):
        self["steps"] += 1
        self["timestamp_ac"] = time.perf_counter()
        self["total_errors_out_of_sync"] = self.total_errors_out_of_sync

        # Car info
        self["packetId"]                = info.graphics.packetId
        self["currentTime"]             = info.graphics.iCurrentTime
        world_position                  = ac.getCarState(self.car_id, acsys.CS.WorldPosition)
        self['world_position_x']          = world_position[2]
        self['world_position_y']          = world_position[0]
        self['world_position_z']          = world_position[1]
        #self['speedKMH']                = ac.getCarState(self.car_id, acsys.CS.SpeedKMH)
        self['speed']                   = ac.getCarState(self.car_id, acsys.CS.SpeedMS)
        # velocity using the car as origin x,y,x = [0, ]
        local_velocity                    = ac.getCarState(self.car_id, acsys.CS.LocalVelocity)
        self['local_velocity_x']          = local_velocity[2]
        self['local_velocity_y']          = local_velocity[0]
        self['local_velocity_z']          = local_velocity[1]

        self['accelX']                  = ac.getCarState(self.car_id, acsys.CS.AccG)[0]
        self['accelY']                  = ac.getCarState(self.car_id, acsys.CS.AccG)[2]
        #self['driverName']              = ac.getDriverName(self.car_id)

        self['accStatus']             = ac.getCarState(self.car_id, acsys.CS.Gas)
        self['brakeStatus']           = ac.getCarState(self.car_id, acsys.CS.Brake)
        self['actualGear']              = ac.getCarState(self.car_id, acsys.CS.Gear)
        #self['actualClutch']              = ac.getCarState(self.car_id, acsys.CS.Clutch)
        self['RPM']                     = ac.getCarState(self.car_id, acsys.CS.RPM)

        #self['dist_l'], self['dist_r'], self['dist_fast_lane']  = self.distance_from_lanes(track)
        self['steerAngle']              = ac.getCarState(self.car_id, acsys.CS.Steer)

        self['yaw']                     = -info.physics.heading
        self['pitch']                   = info.physics.pitch
        self['roll']                    = info.physics.roll

        #self['realtime_leaderboard_position']    = ac.getCarRealTimeLeaderboardPosition(self.car_id) + 1
        #self['car_id']                  = self.car_id

        # Last Force Feedback signal sent to the Wheel [0, …]
        self["LastFF"] = ac.getCarState(self.car_id, acsys.CS.LastFF)
        # Is current Lap invalidated (by going out on the grass) {0, 1}
        self["LapInvalidated"] = ac.getCarState(self.car_id, acsys.CS.LapInvalidated)
        # Position of the car on the track in normalized [0,1]
        self['NormalizedSplinePosition']              = ac.getCarState(self.car_id, acsys.CS.NormalizedSplinePosition)
        self['LapCount']                = ac.getCarState(self.car_id, acsys.CS.LapCount)
        self['BestLap']                 = ac.getCarState(self.car_id, acsys.CS.BestLap)
        self["iLastTime"]               = info.graphics.iLastTime
        self["completedLaps"]           = info.graphics.completedLaps

        # new
        self["numberOfTyresOut"]        = info.physics.numberOfTyresOut
        self["isInPit"]                 = info.graphics.isInPit
        self["penaltyTime"]             = info.graphics.penaltyTime

        # angular velocity of the car, using the car as origin
        angular_velocity                = ac.getCarState(self.car_id, acsys.CS.LocalAngularVelocity)
        self['angular_velocity_x']      = angular_velocity[0]
        self['angular_velocity_y']      = angular_velocity[1]
        self['angular_velocity_z']      = angular_velocity[2]
        # Current velocity vector x,y,z
        velocity                        = ac.getCarState(self.car_id, acsys.CS.Velocity)
        self['velocity_x']              = velocity[0]
        self['velocity_y']              = velocity[1]
        self['velocity_z']              = velocity[2]

        # n_opps = 0
        # carIds = range(1, ac.getCarsCount(), 1)
        # for carId in carIds:
        #     #first we'll check wether there is a car for this id; as soon it returns -1
        #     if str(ac.getCarName(carId)) == '-1':
        #         continue#break
        #     else:
        #         n_opps += 1

        # self['n_opponents']          = n_opps
        self['cgHeight']             = ac.getCarState(self.car_id, acsys.CS.CGHeight)
        self['SlipAngle_fl'], self['SlipAngle_fr'], self['SlipAngle_rl'], self['SlipAngle_rr'] = ac.getCarState(self.car_id, acsys.CS.SlipAngle)

        if self.send_extra_channels:
            # caution this increases the size of the message
            self['tyre_heading_vector']  = ac.getCarState(self.car_id, acsys.CS.TyreHeadingVector)

            # Tyre info
            # self['slip_fl'], self['slip_fr'], self['slip_rl'], self['slip_rr'] = ac.getCarState(self.car_id, acsys.CS.TyreSlip)

            self['tyre_slip_ratio_fl'], self['tyre_slip_ratio_fr'], self['tyre_slip_ratio_rl'], self['tyre_slip_ratio_rr'] = ac.getCarState(self.car_id, acsys.CS.SlipRatio)
            # Self Aligning Torque x,y,z,w
            self['Mz']                   = ac.getCarState(self.car_id, acsys.CS.Mz)
            # Lateral friction coefficient for each tyre
            self['Dy_fl'], self['Dy_fr'], self['Dy_rl'], self['Dy_rr'] = ac.getCarState(self.car_id, acsys.CS.DY)
            self['dynamic_pressure']     = ac.getCarState(self.car_id, acsys.CS.DynamicPressure)
            self['tyre_loaded_radius']   = ac.getCarState(self.car_id, acsys.CS.TyreLoadedRadius)
            self['tyres_load']           = ac.getCarState(self.car_id, acsys.CS.Load)
            self['NdSlip']               = ac.getCarState(self.car_id, acsys.CS.NdSlip)
            self['SuspensionTravel']     = ac.getCarState(self.car_id, acsys.CS.SuspensionTravel)
            self['CamberRad']            = ac.getCarState(self.car_id, acsys.CS.CamberRad)

            # missing IAC data
            # get wheel speeds
            self['wheel_speed_fl'], self['wheel_speed_fr'], self['wheel_speed_rl'], self['wheel_speed_rr'] = ac.getCarState(self.car_id, acsys.CS.WheelAngularSpeed)
            self['fl_tire_temperature_core'], self['fr_tire_temperature_core'], self['rl_tire_temperature_core'], self['rr_tire_temperature_core'] = ac.getCarState(self.car_id, acsys.CS.CurrentTyresCoreTemp)
            # self['fl_tire_thermal_state'], self['fr_tire_thermal_state'], self['rl_tire_thermal_state'], self['rr_tire_thermal_state'] = ac.getCarState(self.car_id, acsys.CS.ThermalState)
            self['fl_damper_linear_potentiometer'], self['fr_damper_linear_potentiometer'], self['rl_damper_linear_potentiometer'], self['rr_damper_linear_potentiometer'] = ac.getCarState(self.car_id, acsys.CS.SuspensionTravel)
            self['fl_wheel_load'], self['fr_wheel_load'], self['rl_wheel_load'], self['rr_wheel_load'] = ac.getCarState(self.car_id, acsys.CS.Load)
            self['fl_tire_pressure'], self['fr_tire_pressure'], self['rl_tire_pressure'], self['rr_tire_pressure'] = ac.getCarState(self.car_id, acsys.CS.DynamicPressure)

            # # TODO verify this interface is correct
            # self['drag_coefficient'] = ac.getCarState(self.car_id, acsys.CS.Aero, '0')
            # self['lift_coefficient_front'] = ac.getCarState(self.car_id, acsys.CS.Aero, '1')
            # self['lift_coefficient_rear'] = ac.getCarState(self.car_id, acsys.CS.Aero, '2')


    def distance_from_lanes(self, track):

        pos = ac.getCarState(self.car_id, acsys.CS.WorldPosition)
        car_width = self.get('CAR_DIM_Z', self["CAR_TRACK"])

        # Minimum distance from lanes - half width of the car
        dist_l = math.sqrt(min([(pos[0] - x)**2 + (pos[2] - y)**2 for x, y in track['left_lane']])) - (car_width / 2)
        dist_r = math.sqrt(min([(pos[0] - x)**2 + (pos[2] - y)**2 for x, y in track['right_lane']])) + (car_width / 2)
        dist_fast_lane = math.sqrt(min([(pos[0] - x)**2 + (pos[2] - y)**2 for x, y in track['fast_lane']]))
        return dist_l, dist_r, dist_fast_lane

    def export(self):
        return json.dumps(self)

class StaticInfo(dict):

    def __init__(self, car_id):
        self.car_id = car_id
        self.done_static_info = False

    # The static car's data should be in content/cars/<car_name>/ui/ui_car.json
    def collect_static_info(self):
        name = ac.getCarName(self.car_id)
        self["TrackName"] = ac.getTrackName(self.car_id)
        self["TrackConfiguration"] = ac.getTrackConfiguration(self.car_id)
        self["WindSpeed"] = ac.getWindSpeed()
        self["WindDirection"] = ac.getWindDirection()
        self["TrackLength"] = ac.getTrackLength(self.car_id)
        self["CarName"] = ac.getCarName(self.car_id)
        self["LastSplits"] = ac.getLastSplits(self.car_id)
        self["isCarInPitlane"] = ac.isCarInPitlane(self.car_id)
        self["isCarInPit"] = ac.isCarInPit(self.car_id)

        self["autoShifterOn"] = info.physics.autoShifterOn
        self["penaltiesEnabled"] = info.static.penaltiesEnabled

        # Front left and right, rear right tires
        fl                      = ac.getCarState(self.car_id, acsys.CS.TyreContactPoint, acsys.WHEELS.FL)
        rl                      = ac.getCarState(self.car_id, acsys.CS.TyreContactPoint, acsys.WHEELS.RL)
        rr                      = ac.getCarState(self.car_id, acsys.CS.TyreContactPoint, acsys.WHEELS.RR)

        self['CAR_WHEEL_R']     = ac.getCarState(self.car_id, acsys.CS.TyreRadius)
        self['CAR_TRACK']       = math.sqrt((rr[0] - rl[0])**2 + (rr[1] - rl[1])**2 + (rr[2] - rl[2])**2)
        self['CAR_WHEELBASE']   = math.sqrt((fl[0] - rl[0])**2 + (fl[1] - rl[1])**2 + (fl[2] - rl[2])**2)


        # The following block works only if the static car info is included as explained above
        try:
            s = 'content/cars/%s/ui/ui_car.json' % name
            with open(s) as json_info:
                    data = json.load(json_info)

            self['CAR_MASS']    = int(data['specs']['weight'][:-2])
            self['CAR_DIM_X']   = float(data['specs']['length'])
            self['CAR_DIM_Y']   = float(data['specs']['height'])
            self['CAR_DIM_Z']   = float(data['specs']['width'])
        except:
            logger.info("Cannot retrieve static data from ui_car.json")

        if self.get("CAR_WHEELBASE", 0) != 0:
            self.done_static_info = True

    def export(self):
        return json.dumps(self)

class Opponent(dict):

    def __init__(self, car_id):
        self.car_id = car_id
        self['id'] = car_id


    def update(self):
        self['world_position']          = ac.getCarState(self.car_id, acsys.CS.WorldPosition)
        self['world_position']          = [self["world_position"][2], self["world_position"][0], self["world_position"][1]]
        self['speedKMH']                = ac.getCarState(self.car_id, acsys.CS.SpeedKMH)
        f, u, l                         = ac.getCarState(self.car_id, acsys.CS.Velocity)
        self['yaw']                     = math.atan2(f, l)


    def export(self):
        return json.dumps(self)


# The data retrieved in the following class is based on raw binary reading of track files
# Since not all track are saved in the same way, the following block works only on certain
# tracks, tested and working on "Magione".
# Track boundary lanes are working fine on Magione, Imola.
class Track(dict):

    def __init__(self, trackName, trackConfig=None):
        self.bounds = dict()
        left_array = []
        right_array = []
        brake_array = []
        throttle_array = []
        speed_array = []
        angle_array = []

        fileDest = "content/tracks/%s" % (trackName)
        if not trackConfig == "" and os.path.isdir("content/tracks/%s/%s" % (trackName, trackConfig)):
            fileDest = "content/tracks/%s/%s" % (trackName, trackConfig)

        fileName = "/ai/fast_lane.ai"

        if not os.path.isfile(fileDest + fileName): return

        ac.console("Loading "+ str(fileDest))
        with open(fileDest + fileName, "rb") as buffer:
            buffer.seek(0)

            header, detailCount, u1, u2 = struct.unpack("4i", buffer.read(4 * 4))

            data_ideal = []
            for i in range(detailCount):
                data_ideal.append(struct.unpack("4f i", buffer.read(4 * 5)))

            data_detail = []
            for i in range(detailCount):
                data_detail.append(struct.unpack("18f", buffer.read(4 * 18)))

            dir_real = 0
            for i in range(detailCount):
                x, y, z, dist, id = data_ideal[i]
                throttle, brake = itemgetter(2, 3)(data_detail[i])
                speed = itemgetter(1)(data_detail[i])
                dir, right, left = itemgetter(4, 6, 7)(data_detail[i])
                dir_real = dir_real + dir
                index_n = i - 1 if i > 0 else detailCount - 1
                angle = math.degrees(math.atan2(data_ideal[index_n][2] - z, x - data_ideal[index_n][0])) * -1

                lx = x + math.cos((-angle - 90) * math.pi / 180) * left
                lz = z - math.sin((-angle - 90) * math.pi / 180) * left

                rx = x + math.cos((-angle + 90) * math.pi / 180) * right
                rz = z - math.sin((-angle + 90) * math.pi / 180) * right

                # left_array.append((rx, rz))
                # right_array.append((lx, lz))


                left_array.append((rz, rx))
                right_array.append((lz, lx))
                throttle_array.append(throttle)
                brake_array.append(brake)
                speed_array.append(max(15, speed))
                angle_array.append(angle)


            self['left_lane'] = left_array
            self['right_lane'] = right_array
            self['fast_lane'] = [(el[2], el[0]) for el in data_ideal]
            self['throttle_arr'] = throttle_array
            self['brake_arr'] = brake_array
            self['speed_arr'] = speed_array
            self['angle_array'] = angle_array


    def export(self):
        return json.dumps(self)
