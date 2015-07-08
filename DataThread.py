"""
This code is written as part of an application for at climate monitor
constisting of an arduino connected to sensors, an SD-card reader and
an LCD-screen and a GUI made by this code. The arduino will have to be
programmed to communicate with the GUI for the monitor to work properly.

The other files required for the program to run are:
Climate_Station.py
Startup.py
LogThread.py
Buttons.py

"""
import numpy as np
from PyQt4 import QtCore
from datetime import date, timedelta

class DataThread(QtCore.QThread):
    
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.dTSerial = None
        self.dFirstData = None
        self.dendData = None
        self.dClimateDataM = None
    
    
    def run(self):
        
        
        #Clear list/Matrix from last time
        self.dClimateDataM = np.empty
        #Allocate array (nRows, nColumns)
        self.dClimateDataM = np.zeros((self.dNData, 9), float)
        
        
        #Clear input buffer if any
        self.dTSerial.flushInput()
        
        #Write to arduino, send command for getting data, the first datapoint
        # and the number of datapoints it should send.
        self.dTSerial.write("ClimateHistory\n")
        self.dTSerial.write(str(self.dFirstData)+"\n")
        self.dTSerial.write(str(self.dNData)+"\n")
        
        #Number of points
        nCounts = 0
                
        #Load data until stop signal
        while True:
              
            #Wait for data
            while self.dTSerial.inWaiting() == 0:
                pass
            
            #Arduino sends: Temp, H, P, Day, Sec 
            #Read line
            line = str(self.dTSerial.readline())
            
            #Check for stop-signal or if all data is loaded
            if ("Stop" in line or nCounts == self.dNData):
                break
            
            
            #Split line
            lineArray = line.split(' , ')
            """
            #Skip failed measurements (T>200 C), should be done by the Arduino            
            if float(lineArray[0]) > 200:
                continue
                """
                
            #For first point get the day and second
            if (nCounts is 0):
                initDay = int(line.split(' , ')[3])
                initSec = int(line.split(' , ')[4])
                
                
            #Add array indices for days, hours and minutes and secs from start
            lineArray.append(0)
            lineArray.append(0)
            lineArray.append(0)
            lineArray.append(0)
            
            #Convert strings to floats
            lineArray = map(float, lineArray)
            
           
            #Save current day and date 
            curDay = lineArray[3]
            #Get current date
            curDate = date(2014,12,31) + timedelta(days=curDay)
            
            #Convert days lineArray[3] and seconds lineArray[4]
            # to date and time in [3][4][5][6][7][8].
            #Get time for at point in seconds and convert to hh:mm
            curSec = lineArray[4]
            #Convert seconds to hh:mm
            m,s=divmod(curSec,60)
            h,m=divmod(m,60)
            #Save year, month and day in array
            lineArray[3] = int(curDate.year)
            lineArray[4] = int(curDate.month)
            lineArray[5] = int(curDate.day)
            #Save hour and minute of day
            lineArray[6] = int(h)
            lineArray[7] = int(m)
            #Column for seconds since start. Made for easy plotting as x-axis.
            lineArray[8] = int((curDay-initDay)*86400 + (curSec - initSec))
            
            #Write the line of data into the climatedata matrix
            self.dClimateDataM[nCounts] = lineArray
            
            #Increment number of points
            nCounts += 1
            #Send signal to update progress bar
            self.emit(QtCore.SIGNAL('updatebar'), nCounts)
        
        
        #Remove allocated zeros from matrix
        self.dClimateDataM = self.dClimateDataM[0:nCounts]
        #Flush input if any
        self.dTSerial.flushInput()
        #Emit signal with the climatedata
        self.emit(QtCore.SIGNAL('getdata'), self.dClimateDataM)
        
        return
        
        