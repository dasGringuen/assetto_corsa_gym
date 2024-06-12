import socket
import json
import logging
import time
import pandas as pd
import numpy as np
import os
import pygame

from AssettoCorsaEnv.car_control import Controls
logger = logging.getLogger(__name__)

MAX_MSG_SIZE = 2**18

class SimulationManagement:
    def __init__(self, config):
        self.config = config
        self.host = config.simulation_management_server_host_name
        self.port = config.simulation_management_server_port

        self.max_msg_size = 2**20

    def send_message(self, message, wait_response=False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(message.encode())
            s.settimeout(5)
            if wait_response:
                data = s.recv(self.max_msg_size).decode()
                return data
            else:
                return None

    def send_reset(self):
        logger.info("sending reset to simulation management server")
        self.send_message("reset")
        time.sleep(1)

    def get_track_info(self):
        data = self.send_message("get_track_info", wait_response=True)
        return eval(data)

    def get_static_info(self):
        static_info = eval(self.send_message("get_static_info", wait_response=True))
        track_full_name = f"{static_info['TrackName']}"
        if static_info['TrackConfiguration']:
            track_full_name += f"-{static_info['TrackConfiguration']}"
        static_info["TrackFullName"] = track_full_name
        return static_info

    def get_config(self):
        return eval(self.send_message("get_config", wait_response=True))


class Client():
    def __init__(self, config):
        self.config = config
        self.vjoy_executed_by_server = config.vjoy_executed_by_server
        self.server_host = config.ego_server_host_name
        self.server_port = config.ego_server_port
        self.simulation_management_server_host_name = config.simulation_management_server_host_name
        self.simulation_management_server_port = config.simulation_management_server_port
        self.state = ServerState()
        self.simulation_management = SimulationManagement(self.config)
        self.socket = None
        self.controls = DriverControls(self.vjoy_executed_by_server)
        self.record_controls_from_client = config.record_controls_from_client

        if self.record_controls_from_client:
            pygame.display.init()
            pygame.joystick.init()
            logger.info(pygame.joystick.get_count())
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            logger.info(self.joystick.get_init())
            logger.info(self.joystick.get_id())
            logger.info(self.joystick.get_name())
            logger.info(self.joystick.get_numaxes())
            logger.info(self.joystick.get_numballs())
            logger.info(self.joystick.get_numbuttons())
            logger.info(self.joystick.get_numhats())

    def reply_to_server(self, msg):
        if not self.socket:
            return
        try:
            self.socket.sendto(msg.encode(), (self.server_host, self.server_port))
        except socket.error as emsg:
            logger.error(f"Error sending to server: {emsg}")
            raise TimeoutError

    def setup_connection(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(2)
        logger.info(f"AC Client. Listening at host: {self.server_host} port: {self.server_port}")

        while True:
            self.reply_to_server("connect")
            try:
                # Receive data from server
                data, _ = self.socket.recvfrom(MAX_MSG_SIZE)
                data = data.decode()
                logger.debug(f"Got from server: {data}")
                if data == "identified":
                    logger.info(f"Client connected on {self.server_port}")
                    break
            except socket.timeout:
                continue
        self.get_servers_input()

    def get_servers_input(self):
        if not self.socket:
            return

        while True:
            try:
                # Receive data from server
                data, _ = self.socket.recvfrom(MAX_MSG_SIZE)
                data = data.decode()
                logger.debug(f"Got from server: {data}")
                if data == "disconnect":
                    logger.info("Server stopped the connection")
                    self.state["done"] = True
                elif data == "identified":
                    logger.info("Server identified")
                else:
                    self.state.parse_server_str(data)
                break
            except socket.timeout:
                continue

    def respond_to_server(self):
        if not self.vjoy_executed_by_server:
            self.controls.apply_local_controls()
        else:
            if not self.socket:
                return
            self.controls["server_steps"] = self.state["steps"] # send back
            self.reply_to_server(self.controls.export())

    def reset(self, send_reset=True):
        if self.socket:
            self.close()
        if send_reset:
            self.simulation_management.send_reset()
        self.controls.set_defaults()
        self.setup_connection()

    def close(self):
        # Send disconnect message
        if not self.vjoy_executed_by_server:
            self.controls.set_defaults()
            self.controls.apply_local_controls()
        self.reply_to_server("disconnect")
        time.sleep(0.1)
        if self.socket:
            self.socket.close()
        self.socket = None

    def step_sim(self):
        self.get_servers_input()
        state = self.state.copy()

        if self.record_controls_from_client:
            pygame.event.pump()
            state["steerAngleManual"] = self.joystick.get_axis(0)
            state["accStatusManual"] = self.joystick.get_axis(1)
            state["brakeStatusManual"] = self.joystick.get_axis(2)
        return state

    def export_track_and_racing_line(self, output_path="."):
        os.makedirs(output_path, exist_ok=True)

        track_info = self.simulation_management.get_track_info()
        static_info = self.simulation_management.get_static_info()

        left_border_x = np.array( track_info['left_lane'] )[:,0]
        left_border_y = np.array( track_info['left_lane'] )[:,1]

        right_border_x = np.array( track_info['right_lane'] )[:,0]
        right_border_y = np.array( track_info['right_lane'] )[:,1]

        fast_lane_x = np.array( track_info['fast_lane'] )[:,0]
        fast_lane_y = np.array( track_info['fast_lane'] )[:,1]

        # save track borders
        track_full_name = f"{static_info['TrackName']}"
        if static_info['TrackConfiguration']:
            track_full_name += f"-{static_info['TrackConfiguration']}"

        track_file_name = f"{output_path}/{track_full_name}.csv"
        df = pd.DataFrame({
            'left_border_x': left_border_x,
            'left_border_y': left_border_y,
            'right_border_x': right_border_x,
            'right_border_y': right_border_y,
            'pos_x': fast_lane_x,
            'pos_y': fast_lane_y
        })
        logger.info(f"Saving track to {track_file_name}")
        df.to_csv(f"{track_file_name}", index=False)

        print(static_info)

        # save racing line for that car -> TODO check if this is car dependent
        racing_line_file_name = f"{output_path}/{static_info['TrackName']}"
        if static_info['TrackConfiguration']:
            racing_line_file_name += f"-{static_info['TrackConfiguration']}"
        #racing_line_file_name += f"-{static_info['CarName']}"
        racing_line_file_name += f"-racing_line.csv"
        logger.info(f"Saving racing line {racing_line_file_name}")

        df = pd.DataFrame({
            'pos_x': fast_lane_x,
            'pos_y': fast_lane_y
        })
        df.to_csv(f"{racing_line_file_name}", index=False)
        return track_full_name, track_file_name, racing_line_file_name, static_info

class ServerState(dict):
    def __init__(self):
        self["done"] = False

    def parse_server_str(self, server_string):
        self.update( eval(server_string) )

class DriverControls(dict):
    def __init__(self, vjoy_executed_by_server=False):
        self.vjoy_executed_by_server = vjoy_executed_by_server

        self.set_defaults()

        #
        self.scale_steer = 0.6 # an input of 1 will be scaled to this value
        if not self.vjoy_executed_by_server:
            logger.warning("Controls will be executed locally and not by the server")
            self.local_controls = Controls()

    def set_defaults(self):
        # steer, acc and brake are in the range [-1, 1]
        self["steer"] = 0
        self["acc"] = -1
        self["brake"] = -1
        self["enable_clutch"] = 0
        self["clutch"] = -1
        self["enable_gear_shift"] = 0
        self["shift_up"] = 0
        self["shift_down"] = 0

    def set_controls(self, steer, acc, brake, enable_clutch=False, clutch=-1,
                     enable_gear_shift=False, shift_up=False, shift_down=False):
        self["steer"] = steer * self.scale_steer
        self["acc"] = acc
        self["brake"] = brake
        self["enable_clutch"] = int(enable_clutch)
        self["clutch"] = clutch
        self["enable_gear_shift"] = int(enable_gear_shift)
        self["shift_up"] = int(shift_up)
        self["shift_down"] = int(shift_down)

    def apply_local_controls(self):
        self.local_controls.set_controls(steer=self["steer"],
                                         acc=self["acc"],
                                         brake=self["brake"],
                                         enable_clutch=self["enable_clutch"],
                                         clutch=self["clutch"],
                                         enable_gear_shift=self["enable_gear_shift"],
                                         shift_up=self["shift_up"],
                                         shift_down=self["shift_down"])

    def export(self):
        return json.dumps(self)