# -*- coding: utf-8 -*-
"""
This Startup object is the one that initializes the serial connection by
prompting the user for a USB port (COM), establishing connection with the 
Arduino and sending the current time and receiving the first day and time where
there is data on the SD card.

This code is written as part of an application for at climate monitor
constisting of an arduino connected to sensors, an SD-card reader and
an LCD-screen and a GUI made by this code. The arduino will have to be
programmed to communicate with the GUI for the monitor to work properly.

The other files required for the program to run are:
Buttons.py
Climate_Station.py
LogThread.py
"""


from PyQt4 import QtGui
import serial
import time
import sys
#To get time in days since 31/12-2014 and seconds since midnight
from datetime import datetime, date

#Object for starting up the system, connecting to the Arduino.
class Startup(QtGui.QWidget):
    #Initiate
    def __init__(self):
        super(Startup, self).__init__()
        #Emission coefficient
        self.emSCoeff = None
        #Serial connection
        self.ardConnect = None
        #Serial Status
        self.status = None
        #Days and second of first measurement
        self.firstDay = None
        self.firstSec = None
        #Serial port name
        self.port = self.showDialog()
        
         
    #Ask for a COM Port for serial connections at startup    
    def showDialog(self):
         
        while(True):
            #Dialog box
            text, ok = QtGui.QInputDialog.getText(self, 'Choose Serial Port', 
                                                  'Choose COM port for serial connection of the Arduino: "COMx"')
            #Check for input errors
            if ok:
                text = text.lower()
                #If the user enters 4 letters (COMx)
                if len(text) is 4:
                    if text and (text[0]=='c') and (text[1]=='o') and (text[2]=='m') and text[3].isdigit():
                        #Break out when a valid string is entered
                        break
                    else:
                        print 'Please write the name of a valid serial port, e.g. "COM1"'
                #If the user enters 5 letters (COMxx)    
                elif len(text) is 5:
                    if text and (text[0]=='c') and (text[1]=='o') and (text[2]=='m') and text[3].isdigit() and text[4].isdigit():
                        #Break out of while loop, when a valid string is entered 
                        break
                    else:
                        print 'Please write the name of a valid serial port, e.g. "COM1"'
                else:
                    print 'Please write the name of a valid serial port, e.g. "COM1"'                    
                        
            #If "Cancel" or X is pressed (Add another option for getting serial port)
            else:
                #Program closes. 
                print "Program is closed"
                sys.exit()
        #Return COM-port in string    
        return text
    
    
    #Method for checking for serial connection and returning a string  
    def initSerial(self):
         
         while True:
             #Check serial connection by exception
             try:
                 #Establish serial connection, resets the arduino
                 self.ardConnect = serial.Serial(self.port , 9600, timeout = 10)
                 #Small delay
                 time.sleep(1)
                 #If connection return status and connection
                 if self.ardConnect is not None:
                     #String for printing serial status         
                     self.status = "Chosen port is: " + self.port.upper() + "  Status: Connected"
                     return self.status, self.ardConnect
                     break
              
            #If connection fails, prompt for serial port again
             except serial.serialutil.SerialException:
                print "Serial Port was unable to open"
                self.port = self.showDialog()
                continue
            
      
            
    #Send the current time, receive day and second for first measurement
    # on SD-card and get the emission factor on the sensor.
    def sendReceive(self): 
        
        #Wait for Arduino to connect
        while(self.ardConnect.inWaiting() == 0):
            pass
        
        #Calculate days since 31/12-2014 and seconds since midnight
        d = datetime.now()
        d1 = date(d.year, d.month, d.day)
        d0 = date(2014,12,31)
        delta = d1-d0
        
        #Convert days and secs to strings
        nDays = str(delta.days)
        secOfDay = str((d.hour*60 + d.minute)*60 + d.second)
        
        timeMes = nDays + " , " + secOfDay
                
        #Read line
        line = self.ardConnect.readline()
          
        #Check if the string contains the command for connection            
        if "SutKaktus" in line:
            #Send days since 31/12-2015 to Arduino
            self.ardConnect.write(str(timeMes)+"\n")
            print "Time is sent "  + str(timeMes)
            
            
        #Variable for first measurement, needed for SD-card readings
        self.firstDay = int(self.ardConnect.readline())
        self.firstSec = int(self.ardConnect.readline())
        #Slet
        print (self.firstDay, self.firstSec)
        #Receive
        self.emSCoeff = float(self.ardConnect.readline())
        #Slet
        print "The emcoeff is " + str(self.emSCoeff)
        
        return self.firstDay, self.firstSec, self.emSCoeff