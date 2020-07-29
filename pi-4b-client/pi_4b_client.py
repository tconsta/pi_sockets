import selectors
import socket
import time
from datetime import datetime, timedelta
# Raspberry Pi libraries:
import RPi.GPIO as GPIO
# pi_version() in /Adafruit_DHT/platform_detect.py has been fixed
# to support Raspberry Pi 4 (BCM2711)
import Adafruit_DHT

SERVER_IP = '192.168.1.9'
SERVER_PORT = 5555

HOSTNAME = 'pi-4b'      # Raspberry Pi 4 Model B
SENSOR_GPIO = 4         # DHT22 Temperature & Humidity Sensor
RELAY_GPIO = 5          # The relay has an inverse control input

# Relay GPIO config
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RELAY_GPIO, GPIO.OUT, initial=GPIO.HIGH)  # turned off by default

LOG_TIMEOUT = 2         # DEBUG in seconds, change to minutes

HOST = 0                # 'pi-4b', 'pi-zero-w'
DATE = 1                # host date
TIME = 2                # host time
SENSOR_DATA1 = 3        # temperature
SENSOR_DATA2 = 4        # humidity (pi-4b)
RELAY_STATE = 5         # state 'on'/'off' (pi-4b)

relay_state = 'off'     # turned off by default

# to send data at a given interval (LOG_TIMEOUT)
last_time_sent = '23:59:59'

# to process incoming requests asynchronously (outgoing are scheduled)
selector = selectors.DefaultSelector()


def get_temperature_and_humidity():

    humid, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, SENSOR_GPIO)
    humid = str(humid)[:4]
    temp = str(temp)[:4]
    return temp, humid


def send_data_to_server(sock):

    current_date = time.strftime('%d') + '.' + time.strftime('%m') + '.' + time.strftime('%Y')
    current_time = time.strftime('%H') + ':' + time.strftime('%M') + ':' + time.strftime('%S')
    temperature, humidity = get_temperature_and_humidity()
    global relay_state

    data_to_send = [HOSTNAME, current_date, current_time, temperature, humidity, relay_state]
    response = ' '.join(data_to_send)

    sock.sendall(response.encode())
    print('sent to server:\n', response)


def control_relay(request):
    global relay_state
    if request == 'turn on relay':
        if relay_state == 'off':
            # turn on relay
            GPIO.output(RELAY_GPIO, GPIO.LOW)
            relay_state = 'on'
    if request == 'turn off relay':
        if relay_state == 'on':
            # turn off relay
            GPIO.output(RELAY_GPIO, GPIO.HIGH)
            relay_state = 'off'


def handle_request_from_server(sock):

    request = sock.recv(1024)
    control_relay(request.decode('utf-8'))


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
