# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:09:11 2015

@author: Emil
"""
from PyQt4 import QtCore
import numpy as np
import time

#A thread for logging, runs simultaneously with the main window
class LogThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.stopNow = False
        self.threadSerial = None
        self.timeNow = None
        self.logTime = 0
        self.start_Thread_Climate = None
        self.end_Thread_Climate = None
        self.iRArray = None
        self.timeArray = None
        #Number of measured points
        self.n = 0
    
    def run(self):
        
        self.n = 0        
        
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
        #Find ud af optimal rækkefølge
        while True:
            #Wait for input
            while (self.threadSerial.inWaiting == 0):
                pass
            
            #Calculate the time
            timeNow = time.clock() - startTime
            
            #Stop after chosen time has passed or stop-button is pressed
            if (timeNow >= self.logTime or self.stopNow):
                self.threadSerial.write("IRStop\n")
                time.sleep(0.5)
                #Slet
                print "I wrote stop"
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
        
        
        #Emits signal: 1. Receive QtCore.SIGNAL('startlogging'), then send self.iRArray and self.timeArray
        self.emit(QtCore.SIGNAL('startlogging'), self.iRArray, self.timeArray)
           
        return    
    
    #Send message to the Arduino to pass on the current climate parameters.
    def getClimate(self):
        
        arConnect = self.threadSerial
        arConnect.write("CopyClimate\n")
        time.sleep(0.1)
        #Read temperature, humidity and pressure.
        #Convert to floats to get rid of \n and then to strings.
        lineTemp = str(round(float(arConnect.readline()), 1))
        lineHum = str(float(arConnect.readline()))
        lineP = str(float(arConnect.readline()))
        #Get the current time
        timeNow = time.strftime("%d/%m-%Y, %H:%M:%S")
        
        climateText = "Temperature: " + lineTemp + " C , Humidity: " + lineHum \
        + " % , Pressure: " + lineP + " mb" + " , Time: " + timeNow
        
        return climateText
            