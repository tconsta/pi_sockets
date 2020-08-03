# Project description
Asynchronous sockets processing using the Selectors module of the Python Standard Library.

The clients are two Raspberry Pi boards (pi-4b and pi-zero-w) and web browsers. DHT22 and DS18B20 sensors are connected to the boards. One of the boards controls a relay module. A server runs on Ubuntu.

![Image](https://raw.githubusercontent.com/tconsta/pi_sockets/master/media/diagram_resized.png)

The server has a simple web interface.

![Image](https://raw.githubusercontent.com/tconsta/pi_sockets/master/media/web%20interface.jpg)

While the hardware looks good, it was only made for temporary testing. For a smart home, I would prefer wireless solutions.

![Image](https://raw.githubusercontent.com/tconsta/pi_sockets/master/media/hardware.jpg)

The server writes data to a .csv file. (A chart was made in Google Sheets.)

![Image](https://raw.githubusercontent.com/tconsta/pi_sockets/master/media/chart.png)

# Requirements
This repository includes source codes for three different hosts. Although I think the code is compatible with any Python 3.7+ version, below are the details.

## Server:
* Ubuntu 20.04 LTS
* Python 3.8.4

## Client 1 (pi-4b):
* Raspberry Pi Model B 2Gb RAM
* Raspbian GNU/Linux 10 (buster)
* Python 3.8.4
* Adafruit_DHT 1.3.10 ([Modified!](https://stackoverflow.com/questions/63030355/can-the-adafruit-dht22-library-be-modified-to-support-raspberry-pi-4-model-b-bc/63035442#63035442)) https://github.com/adafruit/DHT-sensor-library
* RPi.GPIO 0.7.0 https://pypi.org/project/RPi.GPIO/

## Client 2 (pi-zero-w):
* Raspberry Pi Zero W
* Raspbian GNU/Linux 10 (buster)
* Python 3.7.3

## Sensors:
* DHT22 Temperature & Humidity sensor https://www.mouser.com/datasheet/2/737/dht-932870.pdf
* DS18B20 Digital thermometer https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf