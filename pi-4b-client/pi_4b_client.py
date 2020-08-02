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

HOST = 0                # 'pi-4b', 'pi-zero-w'
DATE = 1                # host date
TIME = 2                # host time
SENSOR_DATA1 = 3        # temperature
SENSOR_DATA2 = 4        # humidity (pi-4b)
RELAY_STATE = 5         # state 'on'/'off' (pi-4b)

fan_state = 'off'       # turned off by default
fan_mode = 'manual'
fan_threshold = 25.0    # fan switch-on/off threshold temperature

# to eliminate relay switching at minor temperature fluctuations
TEMP_HYSTERESIS = 1.0

LOG_TIMEOUT = 3         # in minutes

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

    global fan_state

    data_to_send = [HOSTNAME, current_date, current_time, temperature, humidity, fan_state]
    response = ' '.join(data_to_send)

    sock.sendall(response.encode())
    print('sent to server:\n', response)


def fan_auto_control():

    global fan_state
    global fan_threshold

    temperature, _ = get_temperature_and_humidity()

    if fan_state == 'on':
        if float(temperature) < (fan_threshold - TEMP_HYSTERESIS):
            # turn off fan
            GPIO.output(RELAY_GPIO, GPIO.HIGH)
            fan_state = 'off'
    else:
        if float(temperature) > (fan_threshold + TEMP_HYSTERESIS):
            # turn on fan
            GPIO.output(RELAY_GPIO, GPIO.LOW)
            fan_state = 'on'


def handle_request_from_server(sock):

    request = sock.recv(1024).decode('utf-8')
    print('Request from server:\n', request)

    global fan_mode
    global fan_state
    global fan_threshold

    if request == 'turn on fan':
        # turn on fan
        GPIO.output(RELAY_GPIO, GPIO.LOW)
        fan_state = 'on'
        fan_mode = 'manual'
        print('Fan: ', fan_mode, fan_state, fan_threshold)
    elif request == 'turn off fan':
        # turn off fan
        GPIO.output(RELAY_GPIO, GPIO.HIGH)
        fan_state = 'off'
        fan_mode = 'manual'
        print('Fan: ', fan_mode, fan_state, fan_threshold)
    else:
        fan_threshold = float(request.split(',')[1])
        fan_mode = 'auto'
        print('Fan: ', fan_mode, fan_state, fan_threshold)


def sending_timeout_check():

    global last_time_sent
    time_format = '%H:%M:%S'
    last = last_time_sent
    now = time.strftime('%H') + ':' + time.strftime('%M') + ':' + time.strftime('%S')
    time_delta = datetime.strptime(now, time_format) - datetime.strptime(last, time_format)
    if time_delta.days < 0:
        time_delta = timedelta(days=0, seconds=time_delta.seconds, microseconds=time_delta.microseconds)

    if time_delta.seconds > LOG_TIMEOUT*60:
        last_time_sent = now
        return True
    else:
        return False


def event_loop():

    while True:

        if sending_timeout_check():
            send_data_to_server(pi_socket)

        if fan_mode == 'auto':
            fan_auto_control()

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
