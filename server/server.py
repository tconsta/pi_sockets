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

LOG_FILE_PI_4B = 'pi-4b.csv'
LOG_FILE_PI_ZERO_W = 'pi-zero-w.csv'

selector = selectors.DefaultSelector()

turn_on_relay = True


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
        relay_control(client_socket, data[RELAY_STATE])

    if not request:
        selector.unregister(client_socket)
        client_socket.close()


def relay_control(client_socket, relay):

    if not turn_on_relay:
        if relay == 'on':
            # turn off relay
            client_socket.send('turn off relay'.encode())
            print('command sent: turn off relay')
    else:
        if relay == 'off':
            # turn on relay
            client_socket.send('turn on relay'.encode())
            print('command sent: turn on relay')


def save_log(data):

    if data[HOST] == 'pi-4b':
        with open(LOG_FILE_PI_4B, mode='a') as csv_file:
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

        temperature = data[SENSOR_DATA1]

        print(f'saved to {LOG_FILE_PI_ZERO_W}:')
        print(f'temperature = {temperature}')


def handle_http_request(client_socket):

    request = client_socket.recv(4096)
    print(request)
    # parse_http_request(request)
    index_page = open('index.html')
    response = 'HTTP/1.1 200 OK\n\n' + index_page.read()
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
