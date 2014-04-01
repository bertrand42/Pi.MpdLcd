#!/usr/bin/python
from time import sleep
from Adafruit_I2C import Adafruit_I2C
from Adafruit_MCP230xx import Adafruit_MCP230XX 
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import smbus 
import os 
import threading
import signal
import sys
import subprocess

def exit_handler(signal, frame):
       tStop.set()
       if mpIdle is not None:
          mpIdle.terminate()

def displayTrackThread(lcd, stop_event, isOn):
       global mpIdle
       prevMsg = None
       lcdWindowFront = 0
       while not stop_event.is_set():
          mpIdle = subprocess.Popen(['mpc', 'idle'])
          mpIdle.wait()
          mpIdle = None
          msg = getMessage()
          while msg is not None and not stop_event.is_set():
             line = msg[0] 
             if msg == prevMsg:
                if len(line) > 16 and lcdWindowFront <= len(line)-16:
                      dispMsg = line[lcdWindowFront:lcdWindowFront+16]
                      lcdWindowFront = lcdWindowFront + 1
                else:
                      dispMsg = line[0:16]
                      lcdWindowFront = 1
             else:
                prevMsg = msg
                dispMsg = line[0:16]
                lcdWindowFront = 1
             if len(msg) > 1:
                dispMsg = dispMsg + '\n' + msg[1]  
             isOn.set()
             lcd.clear()
             lcd.backlight(lcd.RED)
             lcd.message(dispMsg)
             stop_event.wait(1)
             msg = getMessage()
          isOn.clear()
          lcd.clear()
          lcd.backlight(lcd.OFF)

def getMessage():
       with os.popen("mpc -f '%position%. %name%[\n%title%]' current") as f:
          lines = f.readlines()
       if len(lines) == 0:
          return None
       else:
          # Remove the new line character \n
          lines[0] = lines[0][:-1]
          if len(lines) > 1:
             lines[1] = lines[1][:-1]
          return lines
       
def startDisplayThread():
       global tDisplay
       os.system("mpc stop")
       lcd.clear()
       lcd.backlight(lcd.RED)
       lcd.message("Hello!")
       sleep(2)
       lcd.clear()
       lcd.backlight(lcd.OFF)
       tStop.clear()
       isOn.clear()
       tDisplay = threading.Thread(target=displayTrackThread, args=(lcd, tStop, isOn))
       tDisplay.start()

def stopDisplayThread():
       global tDisplay
       tStop.set()
       if tDisplay is not None:
          tDisplay.join(5)
       tDisplay = None
       os.system("mpc stop")
       lcd.clear()
       lcd.backlight(lcd.OFF)

if __name__ == '__main__':
        os.system("mpc stop")
	exit_requested = False
	signal.signal(signal.SIGINT, exit_handler)
	signal.signal(signal.SIGTERM, exit_handler)

	# use busnum = 0 for raspi version 1 (256MB) and busnum = 1 for version 2
	lcd = Adafruit_CharLCDPlate(busnum = 0)
        tStop = threading.Event()
        isOn = threading.Event()
	tDisplay = None
        mpIdle = None 
        pressing = False
	os.system("mpc volume 85")
	os.system("mpc random off")
	startDisplayThread()

	while not tStop.is_set():
       		if (lcd.buttonPressed(lcd.LEFT)):
                   if not pressing:
                      os.system("mpc pause")
                      os.system("mpc prev")
                      pressing = True
       		elif (lcd.buttonPressed(lcd.RIGHT)):
                   if not pressing:
                      os.system("mpc pause")
                      os.system("mpc next")
                      pressing = True
       		elif (lcd.buttonPressed(lcd.UP)):
                   if not pressing:
                      os.system("mpc volume +5")
                      pressing = True
       		elif (lcd.buttonPressed(lcd.DOWN)):
                   if not pressing:
                      os.system("mpc volume -5")
                      pressing = True
       		elif (lcd.buttonPressed(lcd.SELECT)):
                   if not pressing:
                      pressing = True
                      if isOn.is_set():
                         os.system("mpc stop")
                         isOn.clear()
                      else:
                         os.system("mpc play")
                         isOn.set()
                else:
                    pressing = False            
       		sleep(0.1)

	stopDisplayThread()
	exit(0)
