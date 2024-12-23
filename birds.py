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
import RPi.GPIO as GPIO
import mutagen.mp3
import shutil


#globals
screenChange = 0
fileChange = 0
curScreen = 0
cursPos = 0
cursBound = 0
cTime = time.localtime(time.time())
loopStarted = False
loopPaused = False

GPIO.setup(0,GPIO.OUT)
GPIO.output(0,GPIO.LOW)
GPIO.setup(1,GPIO.IN)
inputMode = False

#initialize lcd
mylcd = I2C_LCD_driver.lcd()

#rtc initializatoin
i2c = board.I2C()
rtc = adafruit_ds3231.DS3231(i2c)
rtcTime = rtc.datetime
time_string = str(rtcTime.tm_year)+"-"+str(rtcTime.tm_mon)+"-"+str(rtcTime.tm_mday)+" "+str(rtcTime.tm_hour)+":"+str(rtcTime.tm_min)+":0"
sudodate = subprocess.Popen(["sudo","date","-s",time_string])

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

#Date and times
alarm = [-1,-1,-1,-1]
alarmTime = ""
device = [-1,-1,-1,-1]	
startTime = 0

scheduleSet = False

#play settings
numLoops = 1
curLoop = numLoops
downTime = 0

#schedule settings
loops = []
alarmTimes = []
sounds = []
startDate = 0
daysInCycle = 0
numCycles = 0
currentCycle = 0

def setTimeForCycle():
	global alarmTimes
	alarmTimes = []
	cycle = 1
	tempAlarm = [-1,-1,-1,-1]
	while cycle <= numCycles:
		mylcd.lcd_clear()
		mylcd.lcd_display_string("X",2,0)
		mylcd.lcd_display_string("Time for Cycle " + str(cycle),1)
		mylcd.lcd_display_string("00:00",2,1)
		index = 0
		timeChange = False
		while index<5:
			if index != 2:
				timeChange = True
			while timeChange:
				mylcd.lcd_display_string("_",2,1+index)
				keys = keypad.pressed_keys
				if keys:
					if index > 2:
						if index == 3 and keys[0] > 5:
							continue
						tempAlarm[index-1] = keys[0]
					else:
						if index == 0 and keys[0] > 2:
							continue 
						tempAlarm[index] = keys[0]  
					mylcd.lcd_display_string(str(keys[0]),2,1+index)
					timeChange = False
			time.sleep(0.1)
			index += 1
		hour = str(tempAlarm[0]) + str(tempAlarm[1])
		minutes = str(tempAlarm[2]) + str(tempAlarm[3])
		alarmTimes.append([hour,minutes])
		cycle+=1
	curScreen = 2
	cursPos = 0
	refresh_screen(1)
		
	

def setSoundForCycle():
	global sounds
	sounds = []
	cycle = 1
	while cycle <= numCycles:
		mylcd.lcd_clear()
		mylcd.lcd_display_string("Sound for Cycle " + str(cycle),1)
		mylcd.lcd_display_string("X",2,0)
		fileChange = 1
		fileNum = 0
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
		sounds.append(fileNum)
		cycle+=1
	curScreen = 3
	cursPos = 0
	refresh_screen(1)
	
def setLoopsForCycle():
	global loops
	loops = []
	cycle = 1	
	while cycle <= numCycles:
		settingsPair = []
		mylcd.lcd_clear()
		mylcd.lcd_display_string("Num Loops ",2,1)
		mylcd.lcd_display_string("Down Time ",3,1)
		mylcd.lcd_display_string("Play Set. for cyc." + str(cycle),1)
		numConfirmed = False
		currentNum = "0"
		index=0
		mylcd.lcd_display_string("X",2,0)
		mylcd.lcd_display_string("_",2,11)
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
					mylcd.lcd_display_string(currentNum,2,11)
					index+=1
					mylcd.lcd_display_string("_",2,11+index)
					time.sleep(0.1)
				else:
					mylcd.lcd_display_string(currentNum,2,11)
					mylcd.lcd_display_string(" ",2,11+index)
					numConfirmed = True
					settingsPair.append(int(currentNum))
		numConfirmed = False
		currentNum = "0"
		index=0
		mylcd.lcd_display_string(" ",2,0)
		mylcd.lcd_display_string("X",3,0)
		mylcd.lcd_display_string("_",3,11)
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
					mylcd.lcd_display_string(currentNum,3,11)
					index+=1
					mylcd.lcd_display_string("_",3,11+index)
					time.sleep(0.1)
				else:
					mylcd.lcd_display_string(currentNum,3,12)
					mylcd.lcd_display_string(" ",3,12+index)
					numConfirmed = True
					settingsPair.append(int(currentNum))
		loops.append(settingsPair)
		cycle+=1
	curScreen = 4
	cursPos = 0
	refresh_screen(1)
			

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
	cursBound = 4 
	mylcd.lcd_clear()
	mylcd.lcd_display_string("B.A.D 2.0",1)
	mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
	mylcd.lcd_display_string("Set Time",2,1)
	mylcd.lcd_display_string("Set Sound",3,1)
	mylcd.lcd_display_string("Play Settings",4,1)
	mylcd.lcd_display_string("Save",2,16)
	mylcd.lcd_display_string("Update",3,14)
	
#prints the time setting screen onto the LCD
def print_time():
	global cursBound 
	cursBound = 3
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Time Settings",1)
	if startDate == 0:
		mylcd.lcd_display_string("Alarm Time",2,1) 
		mylcd.lcd_display_string("Device Time",3,1) 
		if inputMode == False:
			mylcd.lcd_display_string("Input mode on",4,1)
		else:
			mylcd.lcd_display_string("Input mode off",4,1)
		mylcd.lcd_display_string("Enable")
		mylcd.lcd_display_string("Home",4,16)
		mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
		if alarm[0] != -1:
			mylcd.lcd_display_string(alarmTime,2,14)
	else:
		mylcd.lcd_display_string("Set Cycle times",2,1)
		mylcd.lcd_display_string("Device Time",3,1) 
		mylcd.lcd_display_string("Home",4,16)

		
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
	global cursBound
	global numLoops
	global downTime
	
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Play Settings",1,1)
	if startDate == 0:
		cursBound = 4
		mylcd.lcd_display_string("Loops",2,1)
		mylcd.lcd_display_string(str(numLoops),2,12)
		mylcd.lcd_display_string("Down Time",3,1)
		mylcd.lcd_display_string(str(downTime),3,12)
		mylcd.lcd_display_string("Schedule",4,1)
		mylcd.lcd_display_string("Home",4,16)
	else:
		cursBound = 2
		mylcd.lcd_display_string("Set Cycle Loops",2,1)
		mylcd.lcd_display_string("Schedule",3,1)
		mylcd.lcd_display_string("Home",4,16)

def print_schedule():
	global startDate
	global daysInCycle
	global cursBound
	cursBound = 5
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Start Date",1,1)
	mylcd.lcd_display_string("Days in cycle",2,1)
	mylcd.lcd_display_string(str(daysInCycle),2,15)
	mylcd.lcd_display_string("Num cycles",3,1)
	mylcd.lcd_display_string(str(numCycles),3,12)
	mylcd.lcd_display_string("Clear",4,1)
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
			mylcd.lcd_display_string(" ",3,13)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",2,15)
			mylcd.lcd_display_string(" ",3,13)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,0)
			mylcd.lcd_display_string(" ",2,15)
			mylcd.lcd_display_string(" ",3,13)
		if cursPos == 3:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(">",2,15)
			mylcd.lcd_display_string(" ",3,13)
		if cursPos == 4:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(" ",4,0)
			mylcd.lcd_display_string(" ",2,15)
			mylcd.lcd_display_string(">",3,13)
			
			
			
	#If the current screen is the time screen
	if curScreen == 1:
		if screenChange == 1:
			print_time()
		mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
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

	#If the current screen is the sound screen
	if curScreen == 2:
		if screenChange == 1:
				print_sound()
		if startDate == 0:
			mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
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
		else:
			if cursPos == 0:
				mylcd.lcd_display_string(">",2,0)
				mylcd.lcd_display_string(" ",4,15)	
			if cursPos == 1:
				mylcd.lcd_display_string(" ",2,0)
				mylcd.lcd_display_string(">",4,15)
			
			
	#if the current screen is the play screen
	if curScreen == 3:
		if screenChange == 1:
			print_play()
		if startDate == 0:
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
		else:
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

def update():
		path = '/media/birdistheword'
		if not os.path.exists(path):
			mylcd.lcd_clear()
			mylcd.lcd_display_string("No USB Drive")
			time.sleep(5)
			print_main()
			return
		drives = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path,d))]
		if not drives:
			mylcd.lcd_clear()
			mylcd.lcd_display_string("No USB Drive")
			time.sleep(5)
			print_main()
			return
		file_path = ""
		for drive in drives:
			for root, dirs, files in os.walk(drive):
				if 'birds.py' in files:
					file_path = os.path.join(root,'birds.py')
					break
		if file_path == "":
			mylcd.lcd_clear()
			mylcd.lcd_display_string("No birds.py")
			time.sleep(5)
			print_main()
			return
		with open(file_path, 'r') as src:
			with open('/home/birdistheword/birds-git/birds/birds.py', 'w') as dest:
				shutil.copyfileobj(src,dest)
		subprocess.call(['sudo', 'reboot'])
				
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
				elif cursPos == 4:
					update()
				else:
					curScreen = cursPos + 1
					cursPos = 0
					screenChange = 1
	
			
			elif curScreen == 1:

				#set Alarm Time
				if cursPos == 0:
					if startDate == 0:
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
					else:
						setTimeForCycle()

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
					mylcd.lcd_display_string("                   ",3,1)
					mylcd.lcd_display_string("Date 00/00/00",3,1)
					index = 0
					month = 0
					day = 0
					year = 0
					dateChange = False
					while index < 8:
						if index != 2 and index != 5:
							dateChange = True
						while dateChange:
							mylcd.lcd_display_string("_",3,6+index)
							keys = keypad.pressed_keys
							if keys:
								if index < 2:
									if index == 0 and keys[0] > 1:
										continue
									if index == 1 and keys[0] > 2:
										continue
									month *= 10
									month += keys[0]
								elif index > 2 and index < 5:
									if index == 3 and keys[0] > 2 and month == 2:
										continue
									if index == 3 and keys[0] > 3:
										continue
									if index == 4 and month == 2 and keys[0] > 8:
										continue
									if index == 4 and {4,6,9,11}.__contains__(month) and day == 3 and keys[0] > 0:
										continue
									if index == 4 and {1,3,5,7,8,10,12}.__contains__(month) and day == 3 and keys[0] > 1:
										continue
									day *= 10
									day += keys[0]
								elif index > 5:
									year *= 10
									year += keys[0]
								mylcd.lcd_display_string(str(keys[0]),3,6+index)
								dateChange = False
						time.sleep(0.1)
						index += 1
					hour = str(device[0])+str(device[1])
					minutes = str(device[2]) + str(device[3])
					year = 2000 + year
					set_string = str(year)+"-"+str(month)+"-"+str(day)+" "+hour+":"+minutes+":0"
					sudodate = subprocess.Popen(["sudo","date","-s",set_string])
					rtc.datetime = time.struct_time((year,month,day,int(hour),int(minutes),0,0,0,-1))

				if cursPos == 2:		
					inputMode = not inputMode

				if cursPos == 3:
					curScreen = 0
					cursPos = 0
					screenChange = 1
					
			#file selection logic		
			elif curScreen == 2:
				if cursPos == 0:
					if startDate == 0:
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
					else:
						setSoundForCycle()
							
				if cursPos == 1:
					if startDate == 0:
						pygame.mixer.music.load("test.mp3")
						pygame.mixer.music.play(0,0.0)
					else:
						curScreen = 0
						cursPos = 0
						screenChange = 1
				if cursPos == 2:
					curScreen = 0
					cursPos = 0
					screenChange = 1
					
			elif curScreen == 3:
				
				if cursPos == 0:
					if startDate == 0:
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
					else:
						setLoopsForCycle()
				if cursPos == 1:
					if startDate == 0:
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
					else:
						curScreen = 4
						cursPos = 0
						screenChange = 1		
				if cursPos == 2:
					if startDate == 0:
						curScreen = 4
						cursPos = 0
						screenChange = 1
					else:
						curScreen = 0
						cursPos = 0
						screenChange = 1
				if cursPos == 3:
					curScreen = 0
					cursPos = 0
					screenChange = 1

			elif curScreen == 4:
				if cursPos == 0:
					index = 0
					mylcd.lcd_display_string("X",1,0)#change cursor to an X
					mylcd.lcd_display_string("00/00/00",1,12)#display time
					month = 0
					day = 0
					year = 0
					time.sleep(0.1)


					while index < 8:
						if index != 2 and index != 5:
							dateChange = True
						while dateChange:
							mylcd.lcd_display_string("_",1,12+index)
							keys = keypad.pressed_keys
							if keys:
								if index < 2:
									if index == 0 and keys[0] > 1:
										continue
									if index == 1 and keys[0] > 2:
										continue
									month *= 10
									month += keys[0]
								elif index > 2 and index < 5:
									if index == 3 and keys[0] > 2 and month == 2:
										continue
									if index == 3 and keys[0] > 3:
										continue
									if index == 4 and month == 2 and keys[0] > 8:
										continue
									if index == 4 and {4,6,9,11}.__contains__(month) and day == 3 and keys[0] > 0:
										continue
									if index == 4 and {1,3,5,7,8,10,12}.__contains__(month) and day == 3 and keys[0] > 1:
										continue
									day *= 10
									day += keys[0]
								elif index > 5:
									year *= 10
									year += keys[0]
								mylcd.lcd_display_string(str(keys[0]),1,12+index)
								dateChange = False
						time.sleep(0.1)
						index += 1
					
					startDate = datetime.date(2000+year,month,day)
				
				if cursPos == 1:
					numConfirmed = False
					currentNum = "0"
					index=0
					mylcd.lcd_display_string("X",2,0)
					mylcd.lcd_display_string("   ",2,15)
					mylcd.lcd_display_string("_",2,15)
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
								mylcd.lcd_display_string(currentNum,2,15)
								index+=1
								mylcd.lcd_display_string("_",2,15+index)
								time.sleep(0.1)
							else:
								mylcd.lcd_display_string(currentNum,2,15)
								mylcd.lcd_display_string(" ",2,15+index)
								numConfirmed = True
								daysInCycle = int(currentNum)
				if cursPos == 2:
					numConfirmed = False
					currentNum = "0"
					index=0
					mylcd.lcd_display_string("X",3,0)
					mylcd.lcd_display_string("   ",3,12)
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
								numCycles = int(currentNum)
				if cursPos == 3:
					startDate = 0
					numCycles = 0
					numLoops = 0
					currentCycle = 0
					sounds = []
					loops = []
					alarmTimes = []
				if cursPos == 4:
					curScreen = 3
					cursPos = 0
					screenChange = 1
		time.sleep(0.1)
		
	#Check if the current time is equal to the alarm time
	#If it is, play audio
	if inputMode == True and GPIO.input(1) and pygame.mixer.music.get_busy() == False and fileNum != -1:
		GPIO.output(0,GPIO.HIGH)
		pygame.mixer.music.load(dir_list[fileNum])
		pygame.mixer.music.play(0,0.0)
		time.sleep(60)
	
	if pygame.mixer.music.get_busy() == False:
		GPIO.output(0,GPIO.LOW)

	if startDate == 0:
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
					GPIO.output(0,GPIO.HIGH)
					pygame.mixer.music.load(dir_list[fileNum])
					pygame.mixer.music.play(0,0.0)
					time.sleep(60)
				if curLoop <= 0:
					GPIO.output(0,GPIO.LOW)
					curLoop = numLoops
					loopStarted = False
	else:
		if currentCycle < numCycles:
			hour = alarmTimes[currentCycle][0]
			minute = alarmTimes[currentCycle][1]
			if( int(hour) == int(time.strftime("%H")) and int(minute) == int(time.strftime("%M")) or loopStarted):
				if pygame.mixer.music.get_busy() == False and loopStarted == True and loopPaused == False:
					loopPaused = True
					startTime = time.time()
				if (pygame.mixer.music.get_busy() == False and curLoop > 0 and ((time.time() - startTime) > downTime*60 or loopStarted == False) ):
					loopStarted = True
					loopPaused = False
					curLoop-=1
					pygame.mixer.music.load(dir_list[sounds[currentCycle]])
					pygame.mixer.music.play(0,0.0)
					time.sleep(60)
				if curLoop <= 0:
					currentCycle+=1
					curLoop = loops[currentCycle][0]
					downTime = loops[currentCycle][1]
					curLoop = numLoops
					loopStarted = False
