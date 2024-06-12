##############################################################
# Assetto Corsa plugin for data extraction.
# Author: Andrea Serafini
#############################################################

import json
import pickle
import sys
import time
import traceback
import datetime
import ac
import acsys

# setup logger
import ac_logger
ac_logger.setup_logger()

import logging
logger = logging.getLogger(__name__)
logger.info("Starting sensors_par...")

try:
    from structures import Car
    from structures import Track
    from structures import Opponent
    from structures import StaticInfo
    from car_control import Controls
    from record_telemetry import Telemetry
    from ego_server import EgoServer
    from config import config
    if config.vjoy_executed_by_server:
        controls = Controls()
    else:
        controls = None
except:
    logging.exception("An error occurred")
    raise

# Adding external libraries (Socket)
sys.path.insert(
    0, "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\system\\x64\\DLLs")
sys.path.insert(
    0, "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\system\\x64\\Lib")

try:
    import socket
    import threading
    import time
except:
    logging.exception("An error occurred")
    raise

car_export = str()
telemetry = Telemetry()

DONE_STATIC_INFO = False

def reset_car():
    ac.ext_resetCar()
    if controls:
        controls.set_controls(0, -1, -1)

def opponents_server_task():
    global opponents, config

    host = config.opponents_server_host_name
    port = config.opponents_server_port

    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.bind((host, port))
    logger.info("[OPP SERV] Start opponents cars socket on: {}:{}".format(host, port))
    ss.listen(5)

    while True:
        logger.info("[OPP SERV] Waiting for connections.")
        (cs, addr) = ss.accept()

        # Sending number of opponents
        logger.info("[OPP SERV] Client connected, sending data.")
        cs.send(str(len(opponents)).encode('utf8'))

        try:
            while True:
                opponents_list = []
                for opp in opponents:
                    opp.update()
                    opponents_list.append(opp)
                msg = str(len(str(opponents_list))) + "HEADER-END" + str(opponents_list)
                cs.send(msg.encode())
        except:
            logger.info("[OPP SERV] Client disconnected.")
            cs.close()

def simulation_management_server_task():
    global opponents, config

    try:
        host = config.simulation_management_server_host_name
        port = config.simulation_management_server_port

        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ss.bind((host, port))
        logger.info("[MGMT SERV] Start simulation management socket on: {}:{}".format(host, port))
        ss.listen(5)

        while True:
            try:
                logger.info("[MGMT SERV] Waiting for connections.")
                (cs, addr) = ss.accept()

                # Sending number of opponents
                logger.info("[MGMT SERV] Client connected, sending data.")

                while True:
                    # Receive data from the client
                    data = cs.recv(1024).decode("utf8")
                    if not data:
                        break
                    logger.info("[MGMT SERV] Received: {}".format(data))
                    if data == "reset":
                        reset_car()
                    elif data == "get_track_info":
                        track_export = track.export()
                        logger.info(type(track_export))
                        logger.info(len(track_export))
                        cs.send(track.export().encode('utf8'))
                        logger.info("Sending track info")
                    elif data == "get_static_info":
                        static_info.collect_static_info()
                        cs.send(static_info.export().encode('utf8'))
                        logger.info("Sending static info")
                    elif data == "get_config":
                        cs.send(str(config.__dict__).encode('utf8'))
                        logger.info("Sending config")
                    else:
                        logger.info("[MGMT SERV] Unknown command: {}".format(data))
                        break
            except ConnectionResetError:
                cs.close()
                logger.exception("[MGMT SERV] Client disconnected")
            except:
                logger.exception("[MGMT SERV] An error occurred")
    except:
        logger.exception("[OPP SERV] An error occurred")

# The function has to return a string with the plugin name
# Not all the tracks are saved equal in AC, so it can retrieve wrong info
# about the track. (Tested on track "Magione")
def acMain(ac_version):
    global car, track, static_info, opponents, ego_server, telemetry, config, controls

    #Only for specific configurations of the track
    conf = ac.getTrackConfiguration(0)
    if conf == -1:
        track = Track(ac.getTrackName(0))
    else:
        track = Track(ac.getTrackName(0), conf)

    car_id = 0
    car = Car(car_id)
    static_info = StaticInfo(car_id)
    opponents = []

    #Opponents
    carIds = range(1, ac.getCarsCount(), 1)
    for carId in carIds:
        #first we'll check wether there is a car for this id; as soon it returns -1
        if str(ac.getCarName(carId)) == '-1':
            continue#break
        else:
            temp_opp = Opponent(carId)
            opponents.append(temp_opp)
            logger.info("added opponent")


    logger.info("[MAIN] Started.")
    appWindow = ac.newApp("sensors_par")
    ac.setSize(appWindow, 333, 173)

    try:
        ego_server = EgoServer(config, car, controls, telemetry, track=track)
        ego_server.start()  # This will start the server in a separate thread
    except:
        logger.error()
        raise

    # # Starting ego car task
    # try:
    #     t = threading.Thread(target=ego_server_task)
    #     t.daemon = True
    #     t.start()
    # except:
    #     logger.error()
    #     raise

    # Starting opponents task
    try:
        if len(opponents) != 0:
            logger.info("[MAIN] Starting opponent task")
            thread_opps = threading.Thread(target=opponents_server_task)
            thread_opps.daemon = True
            thread_opps.start()
    except:
        logger.error()
        raise

    # Starting management task
    try:
        logger.info("[MAIN] Starting MGR task")
        time.sleep(1)
        thread_mgr = threading.Thread(target=simulation_management_server_task)
        thread_mgr.daemon = True
        thread_mgr.start()
    except:
        logger.error()
        raise

    return "sensors_par"

def acShutdown():
    #global controls
    if controls:
        controls.close()
    logger.info("[MAIN] Stopped.")

# This constantly updates with dynamic car info
def acUpdate(deltaT):
    global car_export, car, track, static_info, telemetry, ego_server

    if not static_info.done_static_info:
        static_info.collect_static_info()
        telemetry.set_static_info(static_info.export())
        return

    if ac.ext_isAltPressed():
        if ac.ext_isButtonPressed("W"):
            ac.ext_takeAStepBack() # same as reset
            logger.info("[MAIN] Step back.")

        if ac.ext_isButtonPressed("R"):
            if telemetry.recording:
                telemetry.stop_recording()
                telemetry.save_telemetry()
                logger.info("[MAIN] Stop recording.")

        if ac.ext_isButtonPressed("E"):
            if not telemetry.recording:
                logger.info("[MAIN] Start recording.")
                telemetry.start_recording()

        if ac.ext_isButtonPressed("R"):
            reset_car()

        if ac.ext_isButtonPressed("T"):
            #log_message("Car: {}".format(ac.getCarName(car.car_id)))
            if controls:
                controls.set_controls(.01, 5., -1)

    # call ego server tick
    ego_server.tick()

    # car.update(track)
    # car_export = car.export()

    # if telemetry:
    #     telemetry.step(eval(car_export))
