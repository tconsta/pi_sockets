import selectors
import socket
import csv

SERVER_IP = '192.168.1.9'
SERVER_PI_PORT = 5555
SERVER_HTTP_PORT = 8080

HOST = 0        # 'pi-4b', 'pi-zero-w'
DATE = 1            # host date
TIME = 2            # host time
SENSOR_DATA1 = 3    # temperature
SENSOR_DATA2 = 4    # humidity (pi-4b)
RELAY_STATE = 5     # state 'on'/'off' (pi-4b)

URLS = [
    '/',
    '/fan/on',
    '/fan/off',
    '/fan/auto',
    '/log/pi4b',
    '/log/pizero']

LOG_FILE_PI_4B = 'pi-4b.csv'
LOG_FILE_PI_ZERO_W = 'pi-zero-w.csv'

VALUE_FILE_PI_4B = 'pi-4b_value.csv'
VALUE_FILE_PI_ZERO_W = 'pi-zero-w_value.csv'

selector = selectors.DefaultSelector()

FAN_THRESHOLD = '27'     # Fan switch-on/off threshold temperature

fan_client_socket = None
fan_state = 'off_'


def pi_server_config():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_IP, SERVER_PI_PORT))
    server_socket.listen()

    selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=accept_pi_connection)


def http_server_config():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_IP, SERVER_HTTP_PORT))
    server_socket.listen()

    selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=accept_http_connection)


def accept_pi_connection(server_socket):

    client_socket, addr = server_socket.accept()
    print('Connection from', addr)
    server_socket.setblocking(False)
    selector.register(fileobj=client_socket, events=selectors.EVENT_READ, data=handle_pi_request)


def accept_http_connection(server_socket):

    client_socket, addr = server_socket.accept()
    print('Connection from', addr)
    server_socket.setblocking(False)
    selector.register(fileobj=client_socket, events=selectors.EVENT_READ, data=handle_http_request)


def handle_pi_request(client_socket):

    request = client_socket.recv(4096)
    print('request from pi:\n', request.decode('utf-8'))

    request = request.decode('utf-8')
    data = request.strip('\n').split(' ')

    save_log(data)

    if data[HOST] == 'pi-4b':
        global fan_client_socket
        fan_client_socket = client_socket

    if not request:
        selector.unregister(client_socket)
        client_socket.close()


def save_log(data):

    if data[HOST] == 'pi-4b':
        with open(LOG_FILE_PI_4B, mode='a') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data[1:])
        # to get the last value (log file can be huge and take a long time to read)
        with open(VALUE_FILE_PI_4B, mode='w') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data[1:])

        temperature = data[SENSOR_DATA1]
        humidity = data[SENSOR_DATA2]
        relay = data[RELAY_STATE]

        print(f'saved to {LOG_FILE_PI_4B}:')
        print(f'temperature = {temperature}, humidity = {humidity}, relay is turned {relay}')

    elif data[HOST] == 'pi-zero-w':
        with open(LOG_FILE_PI_ZERO_W, mode='a') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data[1:])

        with open(VALUE_FILE_PI_ZERO_W, mode='w') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data[1:])

        temperature = data[SENSOR_DATA1]

        print(f'saved to {LOG_FILE_PI_ZERO_W}:')
        print(f'temperature = {temperature}')


def replace_value(text, html_id, shift, value):

    start = text.find(html_id)  # element id
    text = text[:(start + shift)] + value + text[(start + shift + len(value)):]
    return text


def index_view(url):

    print('URL:', url)
    with open('index.html') as index_file:
        index_string = index_file.read()

    with open(VALUE_FILE_PI_4B) as values_file:
        values = values_file.read().split(',')
    pi4b_temperature = values[2]
    pi4b_humidity = values[3]

    with open(VALUE_FILE_PI_ZERO_W) as values_file:
        values = values_file.read().split(',')
    pizero_temperature = values[2].strip('\n')

    shift = 24  # = len('pi4b-temp">Temperature: ')
    index_string = replace_value(index_string, 'pi4b-temp', shift, pi4b_temperature)

    shift = 22  # = len('pi4b-humid">Humidity: ')
    index_string = replace_value(index_string, 'pi4b-humid', shift, pi4b_humidity)

    shift = 26  # = len('pizero-temp">Temperature: ')
    index_string = replace_value(index_string, 'pizero-temp', shift, pizero_temperature)

    shift = 12  # = len('fanState = "')
    index_string = replace_value(index_string, 'fanState', shift, fan_state)

    return index_string


def fan_control(url):

    global fan_state
    if url == '/fan/on':
        fan_state = 'on__'
        fan_client_socket.send('turn on fan'.encode())
        print('command sent: turn on fan')
        return 'Fan on'
    elif url == '/fan/off':
        fan_state = 'off_'
        fan_client_socket.send('turn off fan'.encode())
        print('command sent: turn off fan')
        return 'Fan off'
    elif url == '/fan/auto':
        fan_state = 'auto'
        fan_client_socket.send(('auto fan,' + FAN_THRESHOLD).encode())
        print('command sent: auto fan', FAN_THRESHOLD)
        return 'Fan auto'


def show_log(url):

    if url == '/log/pi4b':
        with open('pi-4b.csv') as log_file:
            log_string = log_file.read()
    else:
        with open('pi-zero-w.csv') as log_file:
            log_string = log_file.read()
    return log_string


def handle_http_request(client_socket):

    request = client_socket.recv(4096)

    parsed = request.decode('utf-8').split(' ')
    url = parsed[1]

    if url not in URLS:
        response = 'HTTP/1.1 404 Not found\n\n'
    else:
        if url == URLS[0]:

            response = index_view(url)
        elif url == URLS[1] or url == URLS[2] or url == URLS[3]:
            response = fan_control(url)
        elif url == URLS[4] or url == URLS[5]:
            response = show_log(url)

        response = 'HTTP/1.1 200 OK\n\n' + response

    client_socket.sendall(response.encode())
    selector.unregister(client_socket)
    client_socket.close()


def event_loop():

    while True:

        # key_events = (key, events)
        # key is the SelectorKey instance corresponding to a ready file object
        # events is a bitmask of events ready on this file object
        key_events = selector.select(timeout=0)

        for key, _ in key_events:
            callback = key.data
            callback(key.fileobj)


if __name__ == '__main__':
    pi_server_config()
    http_server_config()
    event_loop()
