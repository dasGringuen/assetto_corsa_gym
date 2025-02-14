import socket
import threading
import time
import json
from precise_timer import PreciseTimer
from config import Config
from record_telemetry import Telemetry
from profiler import Profiler

import logging
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

MAX_MSG_SIZE = 2**17

class Client(dict):
    def __init__(self, server_socket, addr):
        self.server_socket = server_socket
        self.addr = addr
        self.new_data_avail = False
        self["steer"] = 0
        self["acc"] = -1
        self["brake"] = -1
        self["enable_clutch"] = False
        self["clutch"] = -1
        self["enable_gear_shift"] = False
        self["shift_up"] = False
        self["shift_down"] = False
        self.initialized = False

    def send_reply(self, msg):
        """
        Send a reply to the client
        """
        self.server_socket.sendto(msg.encode(), self.addr)

    def release_lock(self):
        self.lock = False

    def locked_held(self):
        return self.lock

    def get_lock(self):
        if self.lock:
            return False
        self.lock = True
        return True

    def set_lock(self, lock):
        self.lock = lock

    def update(self, data):
        super().update(data)
        self.new_data_avail = True

    def get(self):
        self.new_data_avail = False
        return self

    def export(self):
        return json.dumps(self)

class EgoServer:
    def __init__(self, config, car, controls, telemetry, track):
        self.host = config.ego_server_host_name
        self.port = config.ego_server_port
        self.enable_profiler = config.enable_profiler
        self.server_socket = None
        self.current_client = None
        self.car = car
        self.controls = controls
        self.telemetry = telemetry
        self.track = track
        self.config = config
        self.total_errors_out_of_sync = 0
        self.total_steps = 0
        # self.timer = PreciseTimer(1 / self.config.sampling_freq) # runs in a separate thread
        # self.timer.set_function(self.tick)
        self.socket_open = False

        self.profiler = Profiler(self.enable_profiler)

    def start(self):
        self.thread = threading.Thread(target=self.start_server)
        self.thread.daemon = True
        self.thread.start()

    def close(self):
        # self.timer.stop()
        time.sleep(0.5)

        if self.server_socket and self.socket_open:
            self.server_socket.close()
            self.socket_open = False

        if self.thread:
            self.thread.join()

        self.telemetry.stop_recording()
        self.telemetry.save_telemetry()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_open = True  # Flag to indicate socket is open
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(1.0)
        logging.info("[EGO SERV] Start ego server socket on: {}:{}".format(self.host, self.port))
        logging.info("[EGO SERV] Tick {} Hz Ego: {} Hz".format(self.config.sampling_freq, self.config.ego_sampling_freq))
        try:
            #self.timer.start()
            while self.server_socket and self.socket_open:
                addr = None
                try:
                    # Receive data from client
                    data, addr = self.server_socket.recvfrom(1024)
                    data = data.decode()
                    #logger.info("Received: {}".format(data))
                    if data == "connect":
                        if self.current_client:
                            self.current_client = None
                            logger.warning("New client connected while another client was still connected. Switching to new client.")
                        self.profiler.reset()
                        self.profiler.add_event("connect")
                        self.current_client = Client(self.server_socket, addr) # start with the lock acquired
                        self.current_client.send_reply("identified")
                        time.sleep(0.1) # make sure that the identified message is sent before releasing the lock
                        self.car["steps"] = 0 # reset connection counter
                        logger.debug("Switched to new client {}".format(self.current_client.addr))
                        self.current_client.initialized = True
                    elif data == "disconnect":
                        self.profiler.add_event("disconnect")
                        if self.current_client:
                            self.current_client = None
                            logger.info("Current client disconnected: {}".format(addr))
                        self.profiler.save_to_csv()
                        if self.total_errors_out_of_sync > 0:
                            logger.info("Total out of sync errors: {}".format(self.total_errors_out_of_sync))
                        self.car.total_errors_out_of_sync = 0
                    elif data == "reset":
                        logger.info("Resetting car")
                    else:
                        self.profiler.add_event("reply")
                        data = eval(data)
                        self.current_client.update(data)
                        if data["server_steps"] != self.car["steps"]:
                            self.car.total_errors_out_of_sync += 1
                            #self.car["steps"] = data["server_steps"] # set the server steps to the client steps to get back in sync
                        if self.controls:
                            self.controls.set_controls(steer=self.current_client["steer"],
                                                    acc=self.current_client["acc"],
                                                    brake=self.current_client["brake"],
                                                    enable_clutch=self.current_client["enable_clutch"],
                                                    clutch=self.current_client["clutch"],
                                                    enable_gear_shift=self.current_client["enable_gear_shift"],
                                                    shift_up=self.current_client["shift_up"],
                                                    shift_down=self.current_client["shift_down"])
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    logger.info("Connection to client {} was lost.".format(addr))
                    self.current_client = None
                except OSError as e:
                    if e.winerror == 10038 and not self.socket_open:
                        # This means the socket was closed while recvfrom() was waiting
                        logger.info("Socket operation attempted on closed socket, exiting loop.")
                        break
                    else:
                        raise
                except Exception:
                    logger.exception("An error occurred")
                    if self.current_client:
                        self.current_client.send_reply("disconnect")
                    break
        except Exception:
            logging.exception("An error occurred in the Ego server thread")
        finally:
            if self.socket_open:
                self.close()

    def tick(self):
        #self.profiler.add_event("tick")
        # save telemetry
        if self.telemetry and self.telemetry.recording:
            if (self.total_steps % (self.config.sampling_freq // self.config.telemetry_sampling_freq)) == 0:
                self.car.update(self.track)
                self.telemetry.step(self.car.copy())

        ## if control loop down sample, send telemetry to client
        if self.current_client and self.current_client.initialized:
            if (self.total_steps % (self.config.sampling_freq // self.config.ego_sampling_freq)) == 0:
                try:
                    self.car.update(self.track)
                    car_export = self.car.export()
                    self.profiler.add_event("send")
                    self.current_client.send_reply(car_export)
                except ConnectionResetError:
                    logger.error("Connection to client {} was lost".format(self.current_client.addr))
                    self.current_client = None
                except Exception:
                    logger.exception("An error occurred in the tick function")
                    #self.timer.stop()

        self.total_steps += 1
