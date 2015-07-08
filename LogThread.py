# -*- coding: utf-8 -*-
"""
This code is written as part of an application for at climate monitor
constisting of an arduino connected to sensors, an SD-card reader and
an LCD-screen and a GUI made by this code. The arduino will have to be
programmed to communicate with the GUI for the monitor to work properly.

The other files required for the program to run are:
Startup.py
Climate_Station.py
Buttons.py
DataThread.py

"""
from PyQt4 import QtCore
import numpy as np
import time

#A thread for logging, runs simultaneously with the main window
class LogThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        #Flag for stopping an IR logging
        self.stopNow = False
        #Serial connection
        self.threadSerial = None
        #Timespan for a logging
        self.logTime = 0
        #Beginning and end climate parameters
        self.start_Thread_Climate = None
        self.end_Thread_Climate = None
        #Arrays containing datapoints
        self.iRArray = None
        self.timeArray = None
        #Number of measured points
        self.n = 0
    
    def run(self):
        
        self.n = 0        
        #Get initial climate
        self.start_Thread_Climate = self.getClimate()    
        
        #Allocate arrays
        self.iRArray = np.zeros(100*self.logTime)     
        self.timeArray = np.zeros(100*self.logTime)
        
        #Remove items on the buffer (if any)
        self.threadSerial.flushInput()
        
        #Write command to Arduino
        self.threadSerial.write("IRStart\n")
        
        #Wait for response
        while (self.threadSerial.inWaiting == 0):
                pass
                
        #Get starting time
        startTime = time.clock()    
        
        #Run the logging
        while True:
            #Wait for input
            while (self.threadSerial.inWaiting == 0):
                pass
            
            #Calculate the timepoint
            timeNow = time.clock() - startTime
            
            #Stop after chosen time has passed or stop-button is pressed
            if (timeNow >= self.logTime or self.stopNow):
                #Send stop-signal to arduino
                self.threadSerial.write("IRStop\n")
                #Small delay
                time.sleep(0.5)
                #Remove data on the buffer
                self.threadSerial.flushInput()
                #Get climate at end
                self.end_Thread_Climate = self.getClimate() 
                #Set stop flag to false for next logging
                self.stopNow = False
                break
            
            #Get IR value
            line = self.threadSerial.readline()
            value = float(line)
            
            #Write to arrays
            self.iRArray[self.n] = value
            self.timeArray[self.n] = timeNow
            self.n += 1
            
         
        #Remove empty indices. Go to n because n is incremented one last time
        #before the while loop ends
        self.timeArray = self.timeArray[0:self.n]
        self.iRArray = self.iRArray[0:self.n]
        
        
        #Emits signal: Receive QtCore.SIGNAL('startlogging'), then send self.iRArray and self.timeArray
        self.emit(QtCore.SIGNAL('startlogging'), self.iRArray, self.timeArray)
        
        return    
    
    #Send message to the Arduino to pass on the current climate parameters.
    def getClimate(self):
        #Make serial variable
        arConnect = self.threadSerial
        #Ask for climate parameters
        arConnect.write("CopyClimate\n")
        #Small delay
        time.sleep(0.1)
        #Read temperature, humidity and pressure.
        #Convert to floats to get rid of \n and then to strings.
        lineTemp = str(round(float(arConnect.readline()), 1))
        lineHum = str(float(arConnect.readline()))
        lineP = str(float(arConnect.readline()))
        #Get the current time
        timeNow = time.strftime("%d/%m-%Y, %H:%M:%S")
        
        #Make climate string and return it
        climateText = "Temperature: " + lineTemp + " C , Humidity: " + lineHum \
        + " % , Pressure: " + lineP + " mb" + " , Time: " + timeNow
        
        return climateText
            