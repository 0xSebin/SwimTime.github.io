"""


Group -

SwimTime - Swim your way to success

"""
import machine
import ads1x15
import network
import time
import math
from umqtt.simple import MQTTClient
import micropython
from micropython import const
from machine import Pin

"""
Define constant values
"""


run = False

lapnr = 3  #default lap number
temp = 0.0 
wifi_ssid = "Alfabeta"
wifi_pswd = "12345678"
server = "io.adafruit.com" 
user = "kk2314"
passwd = "674d8794c84d49008c5e0092dc6be24b"
mqtt_temp = "kk2314/feeds/temp"
mqtt_time = "kk2314/feeds/time"
mqtt_rawdata =  "kk2314/feeds/rawdata"
mqtt_control = "kk2314/feeds/control"
mqtt_stat = "kk2314/feeds/stat"
mqtt_debug = "kk2314/feeds/debug"
mqtt_tempalert = "kk2314/feeds/tempalert"

"""
Define pins for LED and buzzer
"""

red = Pin(0, Pin.OUT)    
blue = Pin(2, Pin.OUT)
p12 = machine.Pin(12)
buzz = machine.PWM(p12)		             



#function to blink LED
def blink_LED(colour):
	colour.off()
	time.sleep_ms(50)
	colour.on()
	time.sleep_ms(50)

#setting up I2C for range finder/ set up ADC
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4), freq=100000)
adc = ads1x15.ADS1115(i2c)
adc.gain = 1 #ADS1015_REG_CONFIG_PGA_4_096V

#setting up I2C for temp sens
i2c_temp = machine.I2C(scl=machine.Pin(14), sda=machine.Pin(13), freq=100000)

#Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg):
    global state 
    global run
    global lapnr
    global temp
    
    print((topic, msg))
	#Check for messages only for the control topic
    if topic == b"kk2314/feeds/control":	
    	if msg == b"start":
    		run = True	
    	elif msg.decode() == "temp":
    		get_temp()
    		payload_temp= "{}".format(temp)
    		c.publish(mqtt_temp,payload_temp)
    		print(temp)
    	else:
    		lapnr = int(msg)
    		print(lapnr)
    		

"""
Connect to the wifi
"""

sta_if = network.WLAN(network.STA_IF) 
sta_if.active(True) 
sta_if.scan()
sta_if.connect(wifi_ssid, wifi_pswd)
print('Connecting to Wi-Fi')
#while connecting blink LED and wait
while not sta_if.isconnected():
	blink_LED(red)
	pass
print('Wifi connected')
#Turn red LED on
red.off()

# Turn off ESP8266's AP
ap_if = network.WLAN(network.AP_IF) 
ap_if.active(False)

#Converts the data received from ultrasonic sensor into meters
def convert(data):		
	global distance 
	
	distance = data/10000
	distance = distance/0.000976562 
	distance = (distance/1000)+0.16	


	
#Send a read request and read information of temp sensor as well as convert temp into degree celcius
def get_temp():	
	global temp
	i2c_temp.writeto(0x40,bytearray([0xf3]))
	time.sleep(0.5)
	data=i2c_temp.readfrom(0x40,2)
	tempraw=int.from_bytes(data,"big")
	temp = 175.72 * tempraw / 65536
	temp = temp - 46.85

#sets up the buzzer to run a countdown composed of 3 short beeps and a long one	
def countdown(): 
	count = 0
	freq = 300	
	while count < 3:
		buzz.freq(400)
		buzz.duty(512)
		time.sleep(0.7)
		buzz.duty(1023)
		time.sleep(0.7)
		count = count + 1
	buzz.freq(500)
	buzz.duty(512)
	time.sleep(1.25)
	buzz.duty(1023)	

#converts secs into min and seconds	
def format(sec):
	sec = sec/1000
	mins,secs = divmod(sec, 60)
	secs=round(secs, 3)	
	return (mins, secs)
	
#main() function which executes sensing and mqtt push		
def main(server): 
	global run
	global lapnr
	global nr
	global c
	global mqttConnected
	
	"""	
	Defines which client to connect to. 
	Using adafruit.io broker requires authentification 
	so we also set username and password
	"""	

	c = MQTTClient("Sensor boards", server, user = user, password = passwd)
	c.set_callback(sub_cb)

	#sets flag for mqtt connected	
	if c.connect() == False:
		mqttConnected = True 
		print('MQTT Connected')
			
	#subscribe to the topic where controls are received		
	c.subscribe("kk2314/feeds/control")
	
	
	
	while True:
		
		if True:
		
			c.wait_msg() #blocking check for message 
		
		
			#start timing laps
			if run == True: 
				#reset the run flag   
				
				run = False
				#do countdown		
				countdown()
				c.publish(mqtt_debug,"Started countdown")
				#start timer
				start = time.ticks_ms() 
				c.publish(mqtt_debug,"Timer started")	
				print("go")
				#wait for user to go away from sensor			
				time.sleep(5)   
				#resets statistical variables every beginning of run			
				lap_index =0 
				best_lap=0
				avr_lap = 0
				total_time= 0 
				worst_lap = 0
				#main while loop which continues until lapnr goes to 0 			
				while lapnr > 0:
					blink_LED(blue)				
					data = adc.read(0)    
					convert(data)
				
				
					if distance < 0.80: #add comment 
						lap_time_raw = time.ticks_diff(time.ticks_ms(),start)
						start = time.ticks_ms()
						c.publish(mqtt_debug,"Lap end detected")
						lap_index = lap_index + 1
						
						total_time = total_time + lap_time_raw
						#check if the lap is the slowest 
						if lap_time_raw > worst_lap:
							worst_lap = lap_time_raw
							worst_index = lap_index
						#update average lap_time	
						avr_lap=total_time/lap_index
						#check if lap is the fastest
						if lap_index == 1:
							best_lap= lap_time_raw
							best_index = 1
						elif lap_time_raw < best_lap:
							best_lap = lap_time_raw	
							best_index = lap_index
						
						#format all the statistical values in mins, secs	
						mins_av, secs_av = format(avr_lap)
						mins_bs, secs_bs = format(best_lap)
						mins_ws, secs_ws = format(worst_lap)
						mins_to, secs_to = format(total_time)		
						mins   , secs = format(lap_time_raw) 
						#read current temp 				
						get_temp()
						#send alert if temperature is outside ideal range
						if temp > 21 and temp < 29:
							c.publish(mqtt_tempalert,"Temperature is ideal for a splash, Happy Swimming!")
						elif temp < 21:
							c.publish(mqtt_tempalert,"Careful! We have detected temperature is outside ideal range (Too low)")
						elif temp > 29:	
							c.publish(mqtt_tempalert,"Careful! We have detected temperature is outside ideal range (Too high)")			
					
						#encode all data to JSON - manually to save memory 					
						payload_temp = "{}".format(temp)
						payload = " Lap number {} was: {} m {} s.  ".format(lap_index,mins,secs)
						payload_raw = "{}".format(lap_time_raw/1000)
						payload_stat_av = "Average lap time is : {} m {} s ".format(mins_av,secs_av)
						payload_stat_bs = "Best lap was lap number {} : {} m {} s ".format(best_index,mins_bs,secs_bs)
						payload_stat_ws = "Worst lap was lap number {} : {} m {} s ".format(worst_index,mins_ws,secs_ws)
						payload_stat_to = "Total time is : {} m {} s ".format(mins_to,secs_to)
						#publish converted and raw data to mqtt broker					
						c.publish(mqtt_time,payload)
						c.publish(mqtt_rawdata, payload_raw)
						c.publish(mqtt_temp,payload_temp)
						c.publish(mqtt_stat,payload_stat_av)
						c.publish(mqtt_stat,payload_stat_bs)
						c.publish(mqtt_stat,payload_stat_ws)
						c.publish(mqtt_stat,payload_stat_to)
						c.publish(mqtt_debug,"Data published successfully")
						lapnr = lapnr - 1
						#wait for 10 sec for object to get out of range of sensor 
						if lapnr != 0:
							time.sleep(10)
				c.publish(mqtt_debug,"Done with current run") 		#debug messages
			
			
		else:
			c.check_msg() #non-blocking check for message 
		
		
			 #start timing laps
			if run == True:   
				run = False		
				countdown()
				c.publish(mqtt_debug,"Started countdown")
				#start timer
				start = time.ticks_ms() 
				c.publish(mqtt_debug,"Timer started")	
				print("go")
				#wait for user to go away from sensor			
				time.sleep(5)   
				#resets statistical variables every beginning of run			
				lap_index =0 
				best_lap=0
				avr_lap = 0
				total_time= 0 
				worst_lap = 0
				#main while loop which continues until lapnr goes to 0 			
				while lapnr > 0:				
					data = adc.read(0)    
					convert(data)
				
				
					if distance < 0.80:
						lap_time_raw = time.ticks_diff(time.ticks_ms(),start)
						start = time.ticks_ms()
						c.publish(mqtt_debug,"Lap end detected")
						lap_index = lap_index + 1
						#check if the lap is the best 
						total_time = total_time + lap_time_raw
						if lap_time_raw > worst_lap:
							worst_lap = lap_time_raw
							worst_index = lap_index
						#update average lat_time	
						avr_lap=total_time/lap_index
						#check if lap is the fastest
						if lap_index == 1:
							best_lap= lap_time_raw
							best_index = 1
						elif lap_time_raw < best_lap:
							best_lap = lap_time_raw	
							best_index = lap_index
						
						#format all the statistical values in mins, secs	
						mins_av, secs_av = format(avr_lap)
						mins_bs, secs_bs = format(best_lap)
						mins_ws, secs_ws = format(worst_lap)
						mins_to, secs_to = format(total_time)		
						mins   , secs = format(lap_time_raw) 
						#read current temp 				
						get_temp()
					
						#encode all data to JSON - manually to save memory 					
						payload_temp = "{}".format(temp)
						payload = "{{ Lap number {} was: {} m {} s.  }}".format(lap_index,mins,secs)
						payload_raw = "{}".format(lap_time_raw/1000)
						payload_stat_av = "Average lap time is : {} m {} s ".format(mins_av,secs_av)
						payload_stat_bs = "Best lap was lap number {} : {} m {} s ".format(best_index,mins_bs,secs_bs)
						payload_stat_ws = "Worst lap was lap number {} : {} m {} s ".format(worst_index,mins_ws,secs_ws)
						payload_stat_to = "Total time is : {} m {} s ".format(mins_to,secs_to)
						#push to mqtt broker					
						c.publish(mqtt_time,payload)
						c.publish(mqtt_rawdata, payload_raw)
						c.publish(mqtt_temp,payload_temp)
						c.publish(mqtt_stat,payload_stat_av)
						c.publish(mqtt_stat,payload_stat_bs)
						c.publish(mqtt_stat,payload_stat_ws)
						c.publish(mqtt_stat,payload_stat_to)
						c.publish(mqtt_debug,"Data published successfully")
						lapnr = lapnr - 1
					
						if lapnr != 0:
							time.sleep(10)
				c.publish(mqtt_debug,"Done with current run")
		
				
		
	
	
			
			
	
	c.disconnect()

if __name__ == "__main__":
    main(server)