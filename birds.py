import I2C_LCD_driver
import time
import digitalio
import board
import pygame
import adafruit_matrixkeypad
import os
import subprocess
import mutagen.mp3

#globals
screenChange = 0
fileChange = 0
curScreen = 0
cursPos = 0
cursBound = 0
cTime = time.localtime(time.time())

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

#times
alarm = [-1,-1,-1,-1]
alarmTime = ""
device = [-1,-1,-1,-1]	

#play settings
numLoops = 0
downTime = 0

#prints the main menu screen onto the LCD
def print_main():
	global cursBound 
	cursBound = 2
	mylcd.lcd_clear()
	mylcd.lcd_display_string("B.A.D 2.0",1)
	mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
	mylcd.lcd_display_string("Set Time",2,1)
	mylcd.lcd_display_string("Set Sound",3,1)
	mylcd.lcd_display_string("Play Settings",4,1)
	
#prints the time setting screen onto the LCD
def print_time():
	global cursBound 
	cursBound = 2
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Time Settings",1)
	mylcd.lcd_display_string("Alarm Time",2,1); 
	mylcd.lcd_display_string("Device Time",3,1); 
	mylcd.lcd_display_string("Home",4,16)
	mylcd.lcd_display_string(time.strftime("%H:%M",cTime),1,15)
	if alarm[0] != -1:
		mylcd.lcd_display_string(alarmTime,2,14)
		
#prints the sound settings screen onto the LCD
def print_sound():
	global cursBound 
	cursBound = 2
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Sound Settings",1)
	global currentFile
	if fileNum == -1:
		mylcd.lcd_display_string("File",2,1)
	else:
		mylcd.lcd_display_string(dir_list[fileNum],2,1)
	mylcd.lcd_display_string("Test Audio",3,1)
	mylcd.lcd_display_string("Home",4,16)
	
def print_play():
	global numLoops
	global downTime
	cursBound = 2
	mylcd.lcd_clear()
	mylcd.lcd_display_string("Play Settings",1)
	mylcd.lcd_display_string("Loops",2,1)
	mylcd.lcd_display_string(str(numLoops),2,12)
	mylcd.lcd_display_string("Down Time",3,1)
	mylcd.lcd_display_string(str(downTime),3,12)
	mylcd.lcd_display_string("Home",4,16)
		
	
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
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",2,0)
			mylcd.lcd_display_string(" ",4,0)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,0)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,0)
			
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
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 1:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(">",3,0)
			mylcd.lcd_display_string(" ",4,15)
		if cursPos == 2:
			mylcd.lcd_display_string(" ",2,0)
			mylcd.lcd_display_string(" ",3,0)
			mylcd.lcd_display_string(">",4,15)
		
			


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
									alarm[index-1] = keys[0]
								else:
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
									device[index-1] = keys[0]
								else:
									device[index] = keys[0] 
								mylcd.lcd_display_string(str(keys[0]),3,14+index)
								timeChange = False
						time.sleep(0.1)
						index += 1
					hour = str(device[0])+str(device[1])
					minutes = str(device[2]) + str(device[3])
					set_string = "2023-11-21 "+hour+":"+minutes+":0"
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
					mylcd.lcd_display_string("X",2,0)#change cursor to an X
					mylcd.lcd_display_string("_",2,14)#display time
					time.sleep(0.1)
					while numConfirmed == False:
						keys = keypad.pressed_keys
						if keys:
							lastKey = keys[0]
							if lastKey != "#":
								currentNum += str(lastKey)
                                mylcd.lcd_display_string(currentNum,2,14)
                        else:
							numConfirmed = True
                            numLoops = int(currentNum)
				if cursPos == 1:
					numConfirmed = False
					currentNum = "0"
					mylcd.lcd_display_string("X",3,0)#change cursor to an X
					mylcd.lcd_display_string("_",3,14)#display time
					time.sleep(0.1)
					while numConfirmed == False:
                        keys = keypad.pressed_keys
                        if keys:
                            lastKey = keys[0]
							if lastKey != "#":
								currentNum += str(lastKey)
                                mylcd.lcd_display_string(currentNum,2,14)
                        else:
                            downTime = int(currentNum)
						
				if cursPos == 2:
					curScreen = 0
					cursPos = 0
					screenChange = 1
				
		time.sleep(0.1)
		
	#Check if the current time is equal to the alarm time
	#If it is, play audio
	if alarm[0] != -1 and fileNum != -1:
		hour = str(alarm[0])+str(alarm[1])
		minute = str(alarm[2])+str(alarm[3])
		if ( int(hour) == int(time.strftime("%H")) and int(minute) == int(time.strftime("%M")) ):
			alarm[0] = -1
			pygame.mixer.music.load(dir_list[fileNum])
			pygame.mixer.music.play(-1,0.0)
			  