﻿# -*- coding: utf-8 -*-
"""
This code is written as part of an application for at climate monitor
constisting of an arduino connected to sensors, an SD-card reader and
an LCD-screen and a GUI made by this code. The arduino will have to be
programmed to communicate with the GUI for the monitor to work properly.

The other files required for the program to run are:
Climate_Station.py
Startup.py
LogThread.py
DataThread.py
"""
#For the GUI
from PyQt4 import QtGui, QtCore
#To get current time
import time
#To get time in days since 31/12-2014 and seconds since midnight
from datetime import datetime, date, timedelta
#Work with arrays, files, plots and math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math 
#Import LogThread for running IR logging in parallel with window
from LogThread import LogThread
from DataThread import DataThread



#Class for creating everything inside the main window.
#Also connects to the LogThread() object when an IR logging is run.
class Buttons(QtGui.QWidget):
    #Constructor
    def __init__(self):
        super(Buttons, self).__init__()
        #The logging time i set to 0
        self.logTime = 0
        #Serial connection
        self.buttonSerial = None
        #Combobox is set to seconds
        self.comboStateU = "Seconds"
        #Start and end climate for running measurements
        self.start_Climate = ""
        self.end_Climate = ""
        #First day and first sec sent from Arduino
        self.firstDay = None
        self.firstSec = None
        #Start and end day chosen by user
        self.startDay = None
        self.endDay = None
        #Array of climate data 
        self.climateDataM = None
        #IR-Emission Coefficient 
        self.emCoeff = None
        #Flag for if IR data exists
        self.isData = False
        #Initiate buttons
        self.initButtons()
        #Create a thread for logging, will be run by the 'Start'-button
        self.logThread = LogThread()
        #Create thread object
        self.dataThread = DataThread()
        
      
    #Make the buttons
    def initButtons(self):
        #Variables for layout, nr of pixels   
        self.top = 50
        self.clmPos = 50
        self.logPos = 450
        
        
        
        #Label, climate data
        self.plotLabel = QtGui.QLabel("<b>Climate Data</b>", self)
        self.plotLabel.move(self.clmPos, self.top)
        
        #Label, button info
        self.dateLabel = QtGui.QLabel("<b>Choose a time interval (in days) to plot/save climate data</b>", self)
        self.dateLabel.move(self.clmPos, self.top + 30)
        
        #Label, date chosen
        self.fDayLabel = QtGui.QLabel("Start: <i>None chosen</i>", self)
        self.fDayLabel.move(self.clmPos, self.top + 50) 
        
        #Button for changing first day
        self.fDayButton = QtGui.QPushButton("Change Start", self)
        self.fDayButton.clicked.connect(self.changeDay)
        self.fDayButton.move(self.clmPos + 175, self.top + 50)
        self.fDayButton.resize(80, 20)
        
        #Label, date chosen
        self.lDayLabel = QtGui.QLabel("End:  <i>None chosen</i>", self)
        self.lDayLabel.move(self.clmPos, self.top + 75)
        
        #Button for changing last day
        self.lDayButton = QtGui.QPushButton("Change End", self)
        self.lDayButton.clicked.connect(self.changeDay)
        self.lDayButton.move(self.clmPos + 175, self.top + 70)
        self.lDayButton.resize(80, 20)
        
        #Button for loading climate data
        self.loadData_B = QtGui.QPushButton("Load Climate Data", self)
        self.loadData_B.resize(100,30)
        self.loadData_B.move(self.clmPos, self.top + 120)
        self.loadData_B.clicked.connect(self.loadData_B_Pressed)
        
        #Button for plotting climate
        self.showClimate_B = QtGui.QPushButton("Quick Plot", self)
        self.showClimate_B.resize(90, 30)
        self.showClimate_B.move(self.clmPos, self.top + 175)
        self.showClimate_B.clicked.connect(self.showClimate_B_Pressed)
        
        #Progress bar that shows for loading data and a button
        self.pbar = QtGui.QProgressDialog(self)
        self.pbar.setWindowTitle("Loading...")
        self.pbar.setCancelButton(None)
        self.pbar.setLabelText("Loading data from the Arduino and SD-card \nThis may take several minutes\n\
        The statusbar can't be closed meanwhile ")
        
        #Button for saving chosen data
        self.saveData_B = QtGui.QPushButton("Save Climate Data", self)
        self.saveData_B.resize(100, 30)
        self.saveData_B.move(self.clmPos + 90, self.top + 175)
        self.saveData_B.clicked.connect(self.saveData_B_Pressed)
        
        #Title, left frame
        self.logLabel = QtGui.QLabel("<b> Data Logging for IR sensor </b>", self)
        self.logLabel.move(self.logPos, self.top)
        
        
        #Label, logging time
        self.timeLabel = QtGui.QLabel("<b>Choose logging time</b>", self)
        self.timeLabel.move(self.logPos, self.top + 35)
        
        #Label, show chosen logigng time
        self.timeChosen_L = QtGui.QLabel("The logging time is: 0 seconds                          \
                       ", self)
        self.timeChosen_L.move(self.logPos, self.top + 60)
        
        #Button for changing the logging time value
        self.chaTime_B = QtGui.QPushButton("Change", self)
        self.chaTime_B.resize(80, 30)
        self.chaTime_B.clicked.connect(self.changeTime)
        self.chaTime_B.move(self.logPos, self.top + 80)   
        
        #Combobox to select units
        self.unitBox = QtGui.QComboBox(self)
        self.unitBox.addItem("Seconds")
        self.unitBox.addItem("Minutes")
        self.unitBox.move(self.logPos + 80, self.top + 82)
        #Connect box to function that changes timeChosen_L label
        self.unitBox.activated[str].connect(self.onActivated)
        
        #Label for logging
        self.lowLogLabel = QtGui.QLabel("<b>Run Logging</b>", self)
        self.lowLogLabel.move(self.logPos, self.top + 140)
    
        #Buttons for logging
        self.start_B = QtGui.QPushButton("Start Logging", self)
        self.start_B.clicked.connect(self.start_B_Pressed)
        self.start_B.resize(80, 30)
        self.start_B.move(self.logPos, self.top + 160)
        
        self.stop_B = QtGui.QPushButton("Stop", self)
        self.stop_B.clicked.connect(self.stop_B_Pressed)
        self.stop_B.resize(80, 30)
        self.stop_B.move(self.logPos + 80, self.top + 160)
        
        self.saveIR_B = QtGui.QPushButton("Save IR Data", self)
        self.saveIR_B.clicked.connect(self.writeIRFile)
        self.saveIR_B.resize(80,30)
        self.saveIR_B.move(self.logPos + 2*80, self.top + 160)
        
        #Create empty label for showing if IR logging is running
        self.isRunning_L = QtGui.QLabel("                             ", self)
        self.isRunning_L.setStyleSheet("color: red")
        self.isRunning_L.move(self.logPos, self.top + 200)
        
        #Emission factor button and label
        self.emCoeff_B = QtGui.QPushButton("Change Emission Factor", self)
        self.emCoeff_B.clicked.connect(self.emCoeff_B_Pressed)
        self.emCoeff_B.resize(125, 30)
        self.emCoeff_B.move(self.logPos, self.top + 250)
        
        self.emCoeff_L = QtGui.QLabel(self)
        self.emCoeff_L.move(self.logPos, self.top + 225)
        
        #Button for copying climate parameters
        self.copyClimate_B = QtGui.QPushButton("Copy Climate Parameters to Clipboard", self)
        self.copyClimate_B.minimumSizeHint
        self.copyClimate_B.move(self.logPos - 200, self.top + 350)
        self.copyClimate_B.clicked.connect(self.copyClimate)
        
    #Function for printing the emission coefficient in the window
    # called by mainwindow
    def printEmCoeff(self, emC):
        self.emCoeff_L.setText("The emission factor is: " + str(emC) + "   ")
        
    #When 'Change Start' or 'Change End' is pressed    
    def changeDay(self):
        #Check which button is pressed
        sender = self.sender()
        
        #Loop for user error handling
        while True:
            newDay, ok = QtGui.QInputDialog.getText(self, "Choose a date", "Enter the wanted date in the format: 'dd/mm/yyyy'")
            #Test user input            
            if (ok and len(newDay) is 10 and newDay[2] == "/" and newDay[5] == "/"):
                try:
                    for i in range(0, 10):
                        if i != 2 and i != 5:
                            int(newDay[i])
                #If error in format            
                except ValueError:
                    print "Please write in the given format"
                    continue
                
                #Check which button was pressed and change text in GUI correspondingly
                if "Start" in sender.text():
                    self.startDay = newDay
                    self.fDayLabel.setText("Start: " + self.startDay)
                else:
                    self.endDay = newDay
                    self.lDayLabel.setText("End: " + self.endDay)
                #Break out when parameter and label is changed
                break
            #If the string is the wrong length
            elif ok and len(newDay) is not 10:
                print "Please write in the given format"
            
            #If the user closes the box
            elif not ok:
                break
    
    #Function for checking the user input of the dates. Returns "Failure" if something is wrong.
    #Or send a start measurement and a nr. of measurements for the Arduino to handle.
    def checkUserInput(self):
        
        #Check if dates have been chosen
        if self.startDay is None or self.endDay is None:
            print "Please choose start- and end dates"
            return "Failure"
        
        #Our time starts after 31/12/2014
        startDate = date(2014,12,31)
        
        #Get the start date from the user input string (field variable) and 
        #convert to days since 31/12/2014
        sDay = int(self.startDay[0:2])
        sMonth = int(self.startDay[3:5])
        sYear  = int(self.startDay[6:10])
        #Make a datetime parameter
        sDate = datetime(sYear, sMonth, sDay)
        #Start date in days since 31/12/2014
        deltaStartDays = (sDate.date() - startDate).days
        
        
        #Get the end date from the user input string (field variable) and 
        #convert to days since 31/12/2014
        eDay = int(self.endDay[0:2])
        eMonth = int(self.endDay[3:5])
        eYear  =int(self.endDay[6:10])
        
        eDate = datetime(eYear, eMonth, eDay)
        #End date in days since 31/12/2014
        deltaEndDays = (eDate.date() - startDate).days
        
        
        
        #Check if the start date comes before the end
        if (deltaEndDays < deltaStartDays):
            print "ERROR: End date comes before Start date"
            return "Failure"
        
        #Check if the data exists
        if deltaStartDays < self.firstDay:
            #First date containing data
            firstDate = date(2014,12,31) + timedelta(days=self.firstDay)
            
            #Print error
            print "ERROR: The start date is before the first day containing data."\
            + "\nThe first day with data is: " + str(firstDate.day) + "/" + str(firstDate.month) + "/" + str(firstDate.year)
            return "Failure"
            
        #If the end day is in the future
        if deltaEndDays > (datetime.now().date() - startDate).days:
            print "ERROR: The end day is in the future!"
            return "Failure"
        
        #If the start date is NOT the first day containing data
        #and startDate != endDate, then return first datapoint and number of points.
        if (deltaStartDays != self.firstDay):
            firstData = int(math.floor((deltaStartDays - self.firstDay)*288 -(self.firstSec/300)))
            nData = (deltaEndDays - deltaStartDays + 1)*288
            return firstData, nData
            
        #If the start date is the same as the first day containing data
        if deltaStartDays == self.firstDay:
            #Start from measurement nr. 1
            firstData = 0
            #Find nr. of datapoints
            nData = (deltaEndDays - deltaStartDays)*288 + (24*3600-self.firstSec)/300
            return firstData, nData
            
        
    #Function for loading SD-card date into the
    # matrix called self.climateDataM.
    def loadData_B_Pressed(self):
        
        #Check if input of the chosen dates is invalid
        if (self.checkUserInput() == "Failure"):
            return
            
        #Check if IR logging is running     
        if(self.logThread.isRunning()):
            print "ERROR: IR logging is running! Please stop it before loading data."
            return
        if self.dataThread.isRunning():
            print "Data is already loading, please wait"
            return
        
        #Pass the first data point and number of data points. Number
        #of data points also contain zeros on SD-card made to keep track of time.
        firstData, nData = self.checkUserInput()
        
        #Make a statusbar showing progress
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(nData)
        self.pbar.show()
        self.pbar.setValue(0)
        
        
        #Pass serial connection, first data point and number of data points
        self.dataThread.dTSerial = self.buttonSerial
        self.dataThread.dFirstData = firstData
        self.dataThread.dNData = nData
        #Connect signals for updating pbar and for getting data
        self.connect(self.dataThread, QtCore.SIGNAL('updatebar'), self.updateSBar)
        self.connect(self.dataThread, QtCore.SIGNAL('getdata'), self.getData)
        #Start thread
        self.dataThread.start()
    
    #Function for updating statusbar
    def updateSBar(self, i):
        self.pbar.setValue(i)
        
    #Function (signal slot) for getting data    
    def getData(self, dataM):
        time.sleep(0.5)
        self.pbar.close()
        self.pbar.reset()
        self.climateDataM = dataM
        
        
        
    #Function for writing data to file.
    def saveData_B_Pressed(self):
        #Check if data is loaded
        if self.climateDataM is None:
            print "No data is loaded!"
            return
        
        #Get file-name
        filename, ok = QtGui.QInputDialog.getText(self, "File name", "Choose a file name e. g. 'MyFile\
        \nThe file will be saved at the current directory'")
        #The header should contain the start and end dates of the chosen measurements.
        theHeader = "First day containing data: " + self.startDay + "\nLast day containing data: " + self.endDay
        
        columnNames = ["Temperature (C)", "Humidity (%)", "Pressure (mbar)",\
        "Year", "Month", "Day", "Hour", "Minute", "Seconds since start (for easy plotting)"]        
        #Insert climate parameters in header
        if ok:
            dataFile = pd.DataFrame(self.climateDataM, columns = columnNames)
            dataFile.to_csv(filename+".csv", header = theHeader, sep = ',')
            return
        else:
            return
        
    #Make a plot of the climate parameters
    #Something is wrong with the dates
    def showClimate_B_Pressed(self):
        
        #Check if there's any data
        if self.climateDataM is None:
            print "No data has been loaded!"
            return
        
        boxT = dict(facecolor='red', pad=5, alpha=1)
        boxH = dict(facecolor='blue', pad=5, alpha=1)
        boxP = dict(facecolor='green', pad=5, alpha=1)
        
        #Create figue
        fig = plt.figure(1)
        fig.suptitle("Climate parameters")
        #Get the parameters from the climate matrix
        temp = self.climateDataM[: , 0]
        hum = self.climateDataM[:, 1]
        pres = self.climateDataM[:, 2]
        sec = self.climateDataM[:, 8]
        
        #Get length of matrix to find index of the last parameter
        lengthM = len(self.climateDataM) - 1
        
        #First date of the datapoints, date(year, month, day)
        sDate = date(int(self.climateDataM[0, 3]), int(self.climateDataM[0, 4]), int(self.climateDataM[0, 5]))
        #Last date of the datapoints
        lDate = date(int(self.climateDataM[lengthM, 3]),\
        int(self.climateDataM[lengthM, 4]), int(self.climateDataM[lengthM,5]))
        #Mid date of the datapoints
        mDate =  sDate + timedelta(days=(lDate - sDate).days/2)
        
        #Find first data point in seconds for the first day in the middle
        # and the last day
        mDeltaSecs = (mDate - sDate).days*(24*3600) - self.climateDataM[0, 6]*3600 - self.climateDataM[0, 7]*60
        lDeltaSecs = (lDate - sDate).days*(24*3600) - self.climateDataM[0, 6]*3600 - self.climateDataM[0, 7]*60
        
        
        #Get the index in the climate matrix where the first values are
        # for the mid date and last date
        mRow = np.where(self.climateDataM[:, 8]>=mDeltaSecs)
        mRow = np.asanyarray(mRow)
        mRow = int(mRow[0][0])
        
        lRow = np.where(self.climateDataM[:, 8]>=lDeltaSecs)
        lRow = np.asanyarray(lRow)
        lRow = int(lRow[0][0])
        
        
        #Subplot 1, temp
        spT = plt.subplot(311)
        spT.set_ylabel('Temperature', bbox=boxT)
        spT.axes.get_xaxis().set_visible(False)
        spT.plot(sec, temp, 'ro-')
        
        #Subplot 2, hum
        spH = plt.subplot(312)
        spH.set_ylabel('Humidity', bbox=boxH)
        spH.axes.get_xaxis().set_visible(False)
        spH.plot(sec, hum, 'bo-')
        
        #Subplot 3, pres
        spP = plt.subplot(313)
        spP.set_ylabel('Pressure', bbox=boxP)
        spP.plot(sec, pres, 'go-')
        
        #Show 3 dates on the x-axis
        plt.xticks([0, int(self.climateDataM[mRow, 8]), int(self.climateDataM[lRow, 8])],[str(sDate), str(mDate), str(lDate)], rotation=45)
        plt.tight_layout()
        fig.show()
        
      
    #Function for when user changes the state of the unit combobox
    def onActivated(self):
        if self.comboStateU is "Seconds":
            self.comboStateU = "Minutes"
        else:
            self.comboStateU = "Seconds"
    
    #Function for when the user changes the logging time
    def changeTime(self):
        #User error handling
        
        while True:
            timeC, ok = QtGui.QInputDialog.getText(self, "Choose time", "Enter the logging time")
           
            if ok:
                #Check if user input is an integer
                try:
                    timeC = int(timeC)
                except ValueError:
                    print "Please write an integer"
                    continue
        
                if self.comboStateU is "Seconds":
                    self.timeChosen_L.setText("The logging time is: " + str(timeC) + " seconds")
                    #Set logTime to seconds
                    self.logTime = timeC
                    break
            
                elif self.comboStateU is "Minutes":
                    self.timeChosen_L.setText("The logging time is: " + str(timeC) + " minutes")
                    #Set logTime to 60 seconds pr. minute
                    self.logTime = timeC*60
                    break
        
            #If 'Cancel' or 'X' is pressed
            else:
                return
            
    #When the start button is pressed
            #Lav helst et label der blinker
    def start_B_Pressed(self):
        #Check if thread is already running
        if self.logThread.isRunning():
            print "Logging already running"
            return
        if self.dataThread.isRunning():
            print "Data is loading, please wait"
            return
            
        #Pass on the serial connection, logging time and emission coefficient
        self.logThread.threadSerial = self.buttonSerial
        self.logThread.logTime = self.logTime
        #Send signal to workThread that it shall emit to makeIRPlot()
        self.connect(self.logThread, QtCore.SIGNAL('startlogging'), self.makeIRPlot)
        #Run the funcion run() in the thread
        self.logThread.start()
        #Print to IR-label
        self.isRunning_L.setText("IR-logging Active!")
        
        self.isData = True
    
    #When the stop button is pressed   
    def stop_B_Pressed(self):
        #Set stop flag in the logging thread
        self.logThread.stopNow = True
        
        
    #This function is called automatically after the LogThread() object
    # has been run and has returned the IR parameters.
    def makeIRPlot(self, iRArray,  timeArray):
        #Remove IR logging label. 
        self.isRunning_L.setText("                                    ")
        
        #Show plot after logging is done
        m = len(iRArray)
        plt.ion()
        plt.xlabel("Time (s)")
        plt.ylabel("Temperature (C)")
        plt.suptitle("IR Sensor Logging")
        plt.plot(timeArray[0:m:1], iRArray[0:m:1], 'bo-')
        plt.legend(["IR data-points"])
        plt.show()       
        
    #Function for writing collected IR data to file
    #Right now it saves the file to the same location as the current path.
    #Bør give brugeren mulighed for at vælge path
    def writeIRFile(self):
        #Check if logging is running
        if self.logThread.isRunning():
            print "Please wait for logging to stop before writing a file"
            return
        
        if not self.isData:
            print "No temperature data is available, run logging"
            return
        
        #Acess last run thread to get wanted parameters
        iRArray = self.logThread.iRArray
        timeArray = self.logThread.timeArray
        #Start and end climate parameters for a measurement
        atStart = self.logThread.start_Thread_Climate
        atEnd = self.logThread.end_Thread_Climate 
        #Make header and column names
        theHeader = "Start parameters: ," + str(atStart) + "\n" + "End parameters  : ," + str(atEnd)\
        + "\nTime in seconds, " + "Temperature in C (IR)"
        length = len(timeArray) 
        iRMatrix = np.array([timeArray[1:length], iRArray[1:length]])
        iRMatrix = np.transpose(iRMatrix)
        #Reduce to 2 decimals
        iRMatrix = np.around(iRMatrix, decimals = 2)
        
        #Get file-name
        filename, ok = QtGui.QInputDialog.getText(self, "File name", "Choose a file name e. g. 'MyFile\
        \nThe file will be saved at the current directory'")
        #Insert climate parameters in header
        if ok:
            np.savetxt(filename+".csv", iRMatrix, fmt = "%.2f", header = theHeader, delimiter = ",")
        else:
            return
         
    #Function for the user to change the emission coefficient
    def emCoeff_B_Pressed(self):  
        #Check if logging is running
        if self.logThread.isRunning():
            print "IR logging is running, stop it or wait for it to finish"
            return
        if self.dataThread.isRunning():
            print "Data is loading, please wait"
            return    
        
        #Prompt user for emission coefficient and run error handling      
        while True:
            emissionC, ok = QtGui.QInputDialog.getText(self, "Choose emission coefficient",\
            "Enter the emission coefficient of the material (between 0.10 and 1.00).\
            \nPlease turn off the Arduino, start it again and restart the GUI before continuing.")
            if ok:
                try:
                    emissionC = float(emissionC)
                except ValueError:
                    print "Please write a number"
                    continue
            
                if (float(emissionC) >= 0.10 and float(emissionC) <= 1.00):
                    self.emCoeff = round(emissionC, 2)
                    break
                else:
                    print "Please choose a valid number"
                    continue
            else:
                #Jump out of the function
                return
        
        #Send Emission Coefficient
        self.buttonSerial.write("ChangeEmissivity\n")
        self.buttonSerial.write(str(self.emCoeff))
        
        #Write to GUI
        self.emCoeff_L.setText("The emission factor is: " + str(self.emCoeff))
        return
        
        
    #Send message to the Arduino to pass on the current climate parameters.   
    def getClimate(self):
        
        arConnect = self.buttonSerial
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
        
        
    #Copy climate data into clipboard   
    #Bør skrive i statusbar'en for at bekræfte at den har kopieret data
    def copyClimate(self):
        #Check if logging is running
        if self.logThread.isRunning():
            print "Please wait for logging to stop before getting parameters."
            return
        if self.dataThread.isRunning():
            print "Data is loading, please wait"
            return
            
        clipBoardText = self.getClimate()
        #Make clipboard parameter
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(clipBoardText)