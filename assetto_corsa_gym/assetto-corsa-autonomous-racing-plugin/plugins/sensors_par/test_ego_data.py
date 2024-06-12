import socket
import time
import traceback

def log_error():
    msg = 'Exception: {}\n{}'.format(time.asctime(), traceback.format_exc())
    print(msg)

if __name__ == "__main__":

    # Socket creation
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost",2346))
    old_t = time.time()
    start = time.time()
    delay = []

    inSock = sock.recv(128).decode()
    
    msg_len, full_dict = inSock.split("HEADER-END")
    while int(msg_len) - len(full_dict) > 4096:
        full_dict = full_dict + sock.recv(4096).decode()
    full_dict = full_dict + sock.recv(int(msg_len) - len(full_dict)).decode()
    static_raw = eval(full_dict)