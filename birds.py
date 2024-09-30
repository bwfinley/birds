import I2C_LCD_driver
import time
import digitalio
import configparser
import board
import pygame
import adafruit_matrixkeypad
import os
import subprocess
import adafruit_ds3231
import time
import datetime
import board

import mutagen.mp3

#globals
screenChange = 0
fileChange = 0
curScreen = 0
cursPos = 0
cursBound = 0
cTime = time.localtime(time.time())
loopStarted = False
loopPaused = False

#initialize lcd
mylcd = I2C_LCD_driver.lcd()

#initialize keypad
cols = [digitalio.DigitalInOut(x) for x in (board.D5,board.D6, board.D13)]
rows = [digitalio.DigitalInOut(x) for x in (board.D19, board.D26, board.D21, board.D20)]
keys = ((1,2,3),(4,5,6),(7,8,9),("*",0,"#"))
keypad = adafruit_matrixkeypad.Matrix_Keypad(rows,cols,keys)


#initialize sound
mp3 = mutagen.mp3.MP3("test.mp3")
pygame.mixer.init(frequency = mp3.info.sample_rate)
cwd = os.getcwd()
dir_list = os.listdir(cwd)
dir_list = [x for x in dir_list if x.find("mp3") !=- 1]
currentFile = ""
fileNum = -1
soundLength = 0

#rtc initializatoin
i2c = board.I2C()
rtc = adafruit_ds3231.DS3231(i2c)

#Date and times
alarm = [-1,-1,-1,-1]
alarmTime = ""
device = [-1,-1,-1,-1]	
startTime = 0
startDate = 0
daysInCycle = 0
numCycles = 0
scheduleSet = False

#play settings
numLoops = 1
curLoop = numLoops
downTime = 0

#writes settings to config file
def saveSettings():
	config = configparser.ConfigParser()
	
	config['General'] = {'alarm_time': alarmTime, 'file': fileNum, 'loops': numLoops, 'current_loop': curLoop, 'down_time': downTime}
	
	with open('config.ini', 'w') as configFile:
		config.write(configFile)

#reads ConfigFile
def readConfig():
	global alarmTime, fileNum, numLoops, downTime
	config = configparser.ConfigParser()
	
	config.read('config.ini')
	alarmTime = config.get('General','alarm_time')
	alarm[0] = alarmTime[0]
	alarm[1] = alarmTime[1]
	alarm[2] = alarmTime[3]
	alarm[3] = alarmTime[4]
	fileNum = int(config.get('General','file'))
	numLoops = int(config.get('General','loops'))
	curLoop = int(config.get('General','current_loop'))
	downTime = int(config.get('General','down_time'))
	


#prints the main menu screen onto the LCD
def print_main():
	global cursBound 
	cursBound = 3
	mylcd.lcd_clear()
	mylcd.lcd_display_string("B.A.D 2.0",1)
	mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
	mylcd.lcd_display_string("Set Time",2,1)
	mylcd.lcd_display_string("Set Sound",3,1)
	mylcd.lcd_display_string("Play Settings",4,1)
	mylcd.lcd_display_string("Save",2,16)
	
#prints the time setting screen onto the LCD
def print_time():
	global cursBound 
	cursBound = 2
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Time Settings",1)
	if startDate == 0:
		mylcd.lcd_display_string("Alarm Time",2,1); 
		mylcd.lcd_display_string("Device Time",3,1); 
		mylcd.lcd_display_string("Home",4,16)
		mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
		if alarm[0] != -1:
			mylcd.lcd_display_string(alarmTime,2,14)
	else:
		mylcd.lcd_display_string("Set Cycle times",2,1)
		mylcd.lcd_display_string("Device Time",3,1); 
		mylcd.lcd_display_string("Home",4,16); 

		
#prints the sound settings screen onto the LCD
def print_sound():
	global cursBound 
	cursBound = 2
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Sound Settings",1)
	global currentFile
	if startDate == 0:
		if fileNum == -1:
			mylcd.lcd_display_string("File",2,1)
		else:
			mylcd.lcd_display_string(dir_list[fileNum],2,1)
		mylcd.lcd_display_string("Test Audio",3,1)
		mylcd.lcd_display_string("Home",4,16)
	else:
		mylcd.lcd_display_string("Set Cycle sounds",2,1)
		mylcd.lcd_display_string("Home",4,16)
	
def print_play():
	global numLoops
	global downTime
	cursBound = 3
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Play Settings",1,1)
	if startDate == 0:
		mylcd.lcd_display_string("Loops",2,1)
		mylcd.lcd_display_string(str(numLoops),2,12)
		mylcd.lcd_display_string("Down Time",3,1)
		mylcd.lcd_display_string(str(downTime),3,12)
		mylcd.lcd_display_string("Schedule",4,1)
		mylcd.lcd_display_string("Home",4,16)
	else:
		mylcd.lcd_display_string("Set Cycle Loops")
		mylcd.lcd_display_string("Home",4,16)

def print_schedule():
	global startDate
	global daysInCycle
	cursBound = 5
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Start Date",1,1)
	mylcd.lcd_display_string("Days in cycle",2,1)
	mylcd.lcd_display_string(str(daysInCycle),2,12)
	mylcd.lcd_display_string("Num Cycles",3,1)
	mylcd.lcd_display_string(str(numCycles),3,12)
	mylcd.lcd_display_string("Clear schedule",4,1)
	mylcd.lcd_display_string("Back",4,16)
	
	
#called whenever there is a change on the screen, this can be triggered
#by a time change or a change between menus
def refresh_screen(screenChange):

	#If the current screen is the main screen
	if curScreen == 0:
		if screenChange == 1:
			print_main()
		mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
		#prints proper cursor location
		if cursPos == 0:
			mylcd.lcd_display_string(">",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",2,15)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",2,15)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,0)
			mylcd.lcd_display_string(" ",2,15)
		if cursPos == 3:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(">",2,15)
			
			
	#If the current screen is the time screen
	if curScreen == 1:
		if screenChange == 1:
			print_time()
		mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
		if cursPos == 0:
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,15)
			mylcd.lcd_display_string(">",2,0)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",4,15)
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,15)

	#If the current screen is the sound screen
	if curScreen == 2:
		if screenChange == 1:
			print_sound()
		mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
		if cursPos == 0:
			mylcd.lcd_display_string(">",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,15)	
		if cursPos == 1:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,15)
			
	#if the current screen is the play screen
	if curScreen == 3:
		if screenChange == 1:
			print_play()
		if cursPos == 0:
			mylcd.lcd_display_string(">",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 3:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(">",4,15)

	if curScreen == 4:
		if screenChange == 1:
			print_schedule()
		if cursPos == 0:
			mylcd.lcd_display_string(">",1,0)
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",1,0)
			mylcd.lcd_display_string(">",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",1,0)
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 3:
			mylcd.lcd_display_string(" ",1,0)
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 4:
			mylcd.lcd_display_string(" ",1,0)
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(">",4,15)
			
if os.path.isfile('config.ini'):
	print("read config")
	readConfig()

print_main()

#This is the main loop, this is essentially always running
while True:	

	cTime = time.localtime(time.time())#get current time
	refresh_screen(screenChange)#attempts to refresh the screen at the start of each loop
	screenChange = 0

	keys = keypad.pressed_keys#gets values that have been input into keypad ad stores them in a list
	
	#depending on the value of the key input, the curse should move in different directions
	if keys:
		lastKey = keys[0]

		#move the cursor up
		if lastKey == 2:
			if cursPos == 0:
				cursPos = cursBound
			else:
				cursPos -= 1
		
		#move the cursor down
		elif lastKey == 8:
			if cursPos == cursBound:
				cursPos = 0
			else:
				cursPos += 1
		elif lastKey == 4:
			cursPos = cursPos
		elif lastKey == 6:
			cursPos = cursPos

		#make a selection	
		elif lastKey == 5:

			#if on main screen, just transion to selected screen
			if curScreen == 0:
				if cursPos == 3:
					saveSettings()
				else:
					curScreen = cursPos + 1
					cursPos = 0
					screenChange = 1
	
			
			elif curScreen == 1:

				#set Alarm Time
				if cursPos == 0:
					index = 0
					mylcd.lcd_display_string("X",2,0)#change cursor to an X
					mylcd.lcd_display_string("00:00",2,14)#display time
					time.sleep(0.1)

					#Loops untill 4 digits are input as the time
					while index<5:
						if index != 2:
							timeChange = True
						while timeChange:
							mylcd.lcd_display_string("_",2,14+index)
							keys = keypad.pressed_keys
							if keys:
								if index > 2:
									if index == 3 and keys[0] > 5:
										continue
									alarm[index-1] = keys[0]
								else:
									if index == 0 and keys[0] > 2:
										continue 
									alarm[index] = keys[0]  
								mylcd.lcd_display_string(str(keys[0]),2,14+index)
								timeChange = False
						hour = str(alarm[0]) + str(alarm[1])
						minutes = str(alarm[2]) + str(alarm[3])
						alarmTime = hour+":"+minutes
						time.sleep(0.1)
						index += 1

				#Sets the device time		
				if cursPos == 1: 
					index = 0
					mylcd.lcd_display_string("X",3,0)
					mylcd.lcd_display_string("00:00",3,14)
					time.sleep(0.1)
					while index<5:
						if index != 2:
							timeChange = True
						while timeChange:
							mylcd.lcd_display_string("_",3,14+index)
							keys = keypad.pressed_keys
							if keys:
								if index > 2:
									if index == 3 and keys[0] > 5:
										continue
									device[index-1] = keys[0]
								else:
									if index == 0 and keys[0] > 2:
										continue 
									device[index] = keys[0] 
								mylcd.lcd_display_string(str(keys[0]),3,14+index)
								timeChange = False
						time.sleep(0.1)
						index += 1
					hour = str(device[0])+str(device[1])
					minutes = str(device[2]) + str(device[3])
					set_string = "2024-9-30 "+hour+":"+minutes+":0"
					sudodate = subprocess.Popen(["sudo","date","-s",set_string])
						
				if cursPos == 2:
					curScreen = 0
					cursPos = 0
					screenChange = 1
					
			#file selection logic		
			elif curScreen == 2:
				if cursPos == 0:
					fileChange = 1
					mylcd.lcd_display_string("X",2,0)
					time.sleep(0.1)
					while fileChange == 1:
						keys = keypad.pressed_keys
						if keys:
							lastKey = keys[0]
							if lastKey == 6:
								mylcd.lcd_display_string("                          ",2,1)	
								fileNum += 1
								
							elif lastKey == 4:
								mylcd.lcd_display_string("                          ",2,1)	
								fileNum -= 1
								
							elif lastKey == 5:
								fileChange = 0
						if fileNum == len(dir_list):
							fileNum = 0
						if fileNum < 0:
							fileNum = len(dir_list) - 1
						mylcd.lcd_display_string(dir_list[fileNum],2,1)
						time.sleep(0.05)
						
				if cursPos == 1:
					pygame.mixer.music.load("test.mp3")
					pygame.mixer.music.play(0,0.0)
				if cursPos == 2:
					curScreen = 0
					cursPos = 0
					screenChange = 1
					
			elif curScreen == 3:
				
				if cursPos == 0:
					numConfirmed = False
					currentNum = "0"
					index = 0
					mylcd.lcd_display_string("X",2,0)
					mylcd.lcd_display_string("        ",2,12)
					mylcd.lcd_display_string("_",2,12)
					time.sleep(0.1)
					while numConfirmed == False:
						keys = keypad.pressed_keys
						if keys:
							lastKey = keys[0]
							if lastKey != '#':
								if currentNum == "0":
									currentNum = str(lastKey)
								else:
									currentNum += str(lastKey)
								mylcd.lcd_display_string(currentNum,2,12)
								index+=1
								mylcd.lcd_display_string("_",2,12+index)
								time.sleep(0.1)
							else:
								mylcd.lcd_display_string(currentNum,2,12)
								mylcd.lcd_display_string(" ",2,12+index)
								numConfirmed = True
								numLoops = int(currentNum)
								curLoop = numLoops
				if cursPos == 1:
					numConfirmed = False
					currentNum = "0"
					index=0
					mylcd.lcd_display_string("X",3,0)
					mylcd.lcd_display_string("        ",3,12)
					mylcd.lcd_display_string("_",3,12)
					time.sleep(0.1)
					while numConfirmed == False:
						keys = keypad.pressed_keys
						if keys:
							lastKey = keys[0]
							if lastKey != "#":
								if currentNum == "0":
									currentNum = str(lastKey)
								else:
									currentNum += str(lastKey)
								mylcd.lcd_display_string(currentNum,3,12)
								index+=1
								mylcd.lcd_display_string("_",3,12+index)
								time.sleep(0.1)
							else:
								mylcd.lcd_display_string(currentNum,3,12)
								mylcd.lcd_display_string(" ",3,12+index)
								numConfirmed = True
								downTime = int(currentNum)
				if cursPos == 2:
					curScreen == 4
					cursPos = 0
					screenChange = 1
				if cursPos == 3:
					curScreen = 0
					cursPos = 0
					screenChange = 1

			elif curScreen == 4:
				if cursPos == 0:
					index = 0
					mylcd.lcd_display_string("X",2,0)#change cursor to an X
					mylcd.lcd_display_string("00/00/00",2,14)#display time
					month = 0
					day = 0
					year = 0
					time.sleep(0.1)

					#Loops untill 4 digits are input as the time
					while index < 8:
						if index != 2 and index != 5:
							dateChange = True
						while dateChange:
							mylcd.lcd_display_string("_",3,14+index)
							keys = keypad.pressed_keys
							if keys:
								if index < 2:
									if index == 0 and keys[0] > 1:
										continue
									else:
										month = keys[0]
									if index == 1 and keys[0] > 2:
										continue
									else:
										month *= 10
										month += keys[0]
								elif index > 2 and index < 5:
									if index == 3 and keys[0] > 2 and month == 2:
										continue
									if index == 3 and keys[0] > 3:
										continue
									if index == 4 and month == 2 and keys[0] > 8:
										continue
									if index == 4 and {4,6,9,11}.__contains__(month) and keys[0] > 0:
										continue
									if index == 4 and {1,3,5,7,8,10,12}.__contains__(month) and keys[0] > 1:
										continue
									day *= 10
									day+= keys[0]
								elif index > 5:
									year *= 10
									year += keys[0]
			
								mylcd.lcd_display_string(str(keys[0]),3,14+index)
								dateChange = False
						time.sleep(0.1)
						index += 1
					startDate = datetime.date("20"+str(year),str(month),str(day))
				
				if cursPos == 1:
					numConfirmed = False
					currentNum = "0"
					index=0
					mylcd.lcd_display_string("X",3,0)
					mylcd.lcd_display_string("        ",3,12)
					mylcd.lcd_display_string("_",3,12)
					time.sleep(0.1)
					while numConfirmed == False:
						keys = keypad.pressed_keys
						if keys:
							lastKey = keys[0]
							if lastKey != "#":
								if currentNum == "0":
									currentNum = str(lastKey)
								else:
									currentNum += str(lastKey)
								mylcd.lcd_display_string(currentNum,3,12)
								index+=1
								mylcd.lcd_display_string("_",3,12+index)
								time.sleep(0.1)
							else:
								mylcd.lcd_display_string(currentNum,3,12)
								mylcd.lcd_display_string(" ",3,12+index)
								numConfirmed = True
								daysInCycle = int(currentNum)
				if cursPos == 2:
					keys = keypad.pressed_keys
					if keys:
						lastKey = keys[0]
						if lastKey != "#":
							if currentNum == "0":
								currentNum = str(lastKey)
							else:
								currentNum += str(lastKey)
							mylcd.lcd_display_string(currentNum,3,12)
							index+=1
							mylcd.lcd_display_string("_",3,12+index)
							time.sleep(0.1)
						else:
							mylcd.lcd_display_string(currentNum,3,12)
							mylcd.lcd_display_string(" ",3,12+index)
							numConfirmed = True
							numCycles = int(currentNum)
				if cursPos == 4:
					startDate = 0
					numCycles = 0
					numLoops = 0
				if cursPos == 3:
					curScreen = 3
					cursPos = 0
					screenChange = 1
				
		time.sleep(0.1)
		
	#Check if the current time is equal to the alarm time
	#If it is, play audio
	if alarm[0] != -1 and fileNum != -1:
		hour = str(alarm[0])+str(alarm[1])
		minute = str(alarm[2])+str(alarm[3])
		if ( (int(hour) == int(time.strftime("%H")) and int(minute) == int(time.strftime("%M"))) or loopStarted ):
			if pygame.mixer.music.get_busy() == False and loopStarted == True and loopPaused == False:
				loopPaused = True
				startTime = time.time()
			if (pygame.mixer.music.get_busy() == False and curLoop > 0 and ((time.time() - startTime) > downTime*60 or loopStarted == False) ):
				loopStarted = True
				loopPaused = False
				curLoop-=1
				pygame.mixer.music.load(dir_list[fileNum])
				pygame.mixer.music.play(0,0.0)
				time.sleep(60)
			if curLoop <= 0:
				curLoop = numLoops
				loopStarted = False
			  
