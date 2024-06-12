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

    num_opp = int(sock.recv(1024).decode('utf8'))

    for _ in range(100):

        full_dict = ''
        

        try:
            inSock = sock.recv(32).decode()
            try:
                # Buffered reading (Header - "HEADER-END" - Payload model)
                msg_len, full_dict = inSock.split("HEADER-END")
                while int(msg_len) - len(full_dict) > 4096:
                    full_dict = full_dict + sock.recv(4096).decode()
                full_dict = full_dict + sock.recv(int(msg_len) - len(full_dict)).decode()
            except:
                print("Errore!")
                log_error()


            # Data dictionary creation
            raw = eval(full_dict)

            
            stamp = time.time()
            delay.append(stamp - old_t)
            old_t = stamp

            for el in raw:
                print("--------------------------------------------")
                print("Macchina ", el.get("id"))
                print("Vel:", el.get("speedKMH"))
                print("Yaw:", el.get("yaw"))
                print("--------------------------------------------")
        except:
            print("Errore out!")
            log_error()

    print("AVG (secs between msgs):", sum(delay) / len(delay))
    print("# of messages received:", len(delay))
    end = time.time()
    print("Total elapsed:", end - start)
    print(num_opp)
