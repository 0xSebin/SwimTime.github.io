# [Swimtime](https://swimtime.github.io)

SwimTime is the IoT project for EE3-24 Embedded Systems from team TAY. SwimTime is a device which accompanies the user in the swimming pool and records and tracks your laps other relavant data for your workout.

## The Code

The main.py file contains all the functions and logic used by the ESP8266. In order for the device to function correctly both main.py and ads1115.py must be uploaded on the board. The ads1115.py contains functions used for driving the ADC Analog-to-Digital. The ADC is used to convert the analog output of our ultrasonic range finder sensor into digital and then push it to the board via I2C. The temperature and humidity  sensor is in turn linked directly to the board as it has an I2C interface.



## MQTT Data and Cloud

MQTT protocol is used to transmit and receive data on the esp8266. We use the open-broker provided by io.adafruit.com which also provides a dashboards for interacting and analysis data recived from the sensor. Through the dashboard you are able to select number of laps and send the start command as well as see your lap times, statistical data about your fastest and slowest runs and a temperatur indicator which dispays the water temperature. 



## Usage

### Basic Usage

To use the devide just connect to power (for simplicity we use the usb port) and pres the reset button. The device will configure automatically and connect to the Wi-Fi (when the red LED is on the board is successfully connected to the Wi-Fi). Then just select the number of laps you want to complete and pres start on the dashboard. The board will initiate the countdown and will start timing you laps after the countdown (you should hear a buzzer beep 3 times). 





## Copyright and License

Copyright 2018 Imperial College London. 
