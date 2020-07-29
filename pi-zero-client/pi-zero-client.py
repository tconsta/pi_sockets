import selectors
import socket
import time
import os
import glob
from datetime import datetime, timedelta

SERVER_IP = '192.168.1.9'
SERVER_PORT = 5555

HOSTNAME = 'pi-zero-w'  # Raspberry Pi Zero W
SENSOR_GPIO = 4         # DS18B20 Digital thermometer

LOG_TIMEOUT = 2         # DEBUG in seconds, change to minutes

HOST = 0                # 'pi-4b', 'pi-zero-w'
DATE = 1                # host date
TIME = 2                # host time
SENSOR_DATA1 = 3        # temperature

# Sensor config
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


# to send data at a given interval (LOG_TIMEOUT)
last_time_sent = '23:59:59'

# to process incoming requests asynchronously (outgoing are scheduled)
selector = selectors.DefaultSelector()


def get_temp_raw():

    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def get_temperature():

    lines = get_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = get_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return str(round(temp_c, 2))


def send_data_to_server(sock):

    current_date = time.strftime('%d') + '.' + time.strftime('%m') + '.' + time.strftime('%Y')
    current_time = time.strftime('%H') + ':' + time.strftime('%M') + ':' + time.strftime('%S')
    temperature = get_temperature()

    data_to_send = [HOSTNAME, current_date, current_time, temperature]
    response = ' '.join(data_to_send)

    sock.sendall(response.encode())
    print('sent to server:\n', response)


def handle_request_from_server(sock):

    request = sock.recv(1024)
    print(request.decode('utf-8'))
    # do something else


def sending_timeout_check():

    global last_time_sent
    time_format = '%H:%M:%S'
    last = last_time_sent
    now = time.strftime('%H') + ':' + time.strftime('%M') + ':' + time.strftime('%S')
    time_delta = datetime.strptime(now, time_format) - datetime.strptime(last, time_format)
    if time_delta.days < 0:
        time_delta = timedelta(days=0, seconds=time_delta.seconds, microseconds=time_delta.microseconds)

    if time_delta.seconds > LOG_TIMEOUT:  # DEBUG: change to LOG_TIMEOUT*60
        last_time_sent = now
        return True
    else:
        return False


def event_loop():

    while True:

        if sending_timeout_check():
            send_data_to_server(pi_socket)

        # Tracking incoming data:
        key_events = selector.select(timeout=0)
        for key, _ in key_events:
            callback = key.data
            callback(key.fileobj)


pi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
pi_socket.connect((SERVER_IP, SERVER_PORT))
pi_socket.setblocking(False)
selector.register(pi_socket, selectors.EVENT_READ, data=handle_request_from_server)

if __name__ == '__main__':

    event_loop()
