# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 10:25:55 2015

@author: Emil

This Startup object is the one that initializes the serial connection by
prompting the user for a USB port (COM), establishing connection with the 
Arduino and sending the current time and receiving the first day and time where
there is data on the SD card.

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
        self.emSCoeff = None
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
                        #(Add a dialog box)
                        print 'Please write the name of a valid serial port, e.g. "COM1"'
                #If the user enters 5 letters (COMxx)    
                elif len(text) is 5:
                    if text and (text[0]=='c') and (text[1]=='o') and (text[2]=='m') and text[3].isdigit() and text[4].isdigit():
                        #Break out of while loop, when a valid string is entered 
                        break
                    else:
                        #(Add a dialog box)
                        print 'Please write the name of a valid serial port, e.g. "COM1"'
                else:
                    print 'Please write the name of a valid serial port, e.g. "COM1"'                    
                        
            #If "Cancel" or X is pressed (Add another option for getting serial port)
            else:
                #Program closes. Might need a different approach.
                print "Program is closed"
                sys.exit()
            
        return text
    
    
    #Method for checking for serial connection and returning a string  
    def initSerial(self):
         
         
         while True:
             #Check serial connection by exception
             try:
                 #The Arduino is reset
                 self.ardConnect = serial.Serial(self.port , 9600, timeout = 10)
                 
                 time.sleep(1)
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
            
      
            
    #Send the current time after startup for the Arduino
    def sendReceive(self): 
        
        #Wait for Arduino to connect
        while(self.ardConnect.inWaiting() == 0):
            pass
        
        #Calculate days since 31/12-2014 and seconds since midnight
        self.d = datetime.now()
        self.d1 = date(self.d.year, self.d.month, self.d.day)
        self.d0 = date(2014,12,31)
        self.delta = self.d1-self.d0
        
        #Convert days and secs to strings
        self.nDays = str(self.delta.days)
        self.secOfDay = str((self.d.hour*60 + self.d.minute)*60 + self.d.second)
        
        self.timeMes = self.nDays + " , " + self.secOfDay
        
        #while True:
        #Read line
        self.line = self.ardConnect.readline()
          
            #Check if the string contains the command for connection            
        if "SutKaktus" in self.line:
                #Calculate and send days since 31/12-2015
            self.ardConnect.write(str(self.timeMes)+"\n")
            print "Time is sent "  + str(self.timeMes)
            
            
        #Variable for first measurement, needed for SD-card readings
        self.firstDay = int(self.ardConnect.readline())
        self.firstSec = int(self.ardConnect.readline())
        print (self.firstDay, self.firstSec)
        #Receive
        self.emSCoeff = float(self.ardConnect.readline())
        print "The emcoeff is " + str(self.emSCoeff)
        
        return self.firstDay, self.firstSec, self.emSCoeff