# -*- coding: utf-8 -*-
"""
Created on Sun Jun 07 12:41:04 2015

@author: Emil

This code could not have been written if it wasn't for the tutorial on:
http://zetcode.com/gui/pyqt4/
Small parts an pieces have been taken directly from there.

"""
#For the GUI
import sys
from PyQt4 import QtCore, QtGui
#To get current time
import time
#To get time in days since 31/12-2014 and seconds since midnight
from datetime import datetime, date, timedelta
#Work with arrays, files, plots and math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math 
#Other parts of the code
from Startup import Startup
from LogThread import LogThread


#Main class, initiates main window and other objects
class ClimateStationWindow(QtGui.QMainWindow):
    
    def __init__(self):
        #Inherit from QtGui.QMainWindow and initiate
        super(ClimateStationWindow, self).__init__()
        self.things = None
        self.firstDay = None
        self.firstSec = None
        self.emCoeffS = None
        self.serialStatus = None
        self.serialConnection = None
        self.initUI()
        self.runMain()
    
    def initUI(self):
        #Window geometry
        self.setGeometry(100, 75, 750, 450)
        self.setWindowTitle("Climate Station Monitor")
        
        #Lock the window size
        self.setMinimumSize(750, 450)
        self.setMaximumSize(750, 450)
        
    #Draw lines in window 
    def paintEvent(self, e):

        qPainter = QtGui.QPainter()
        qPainter.begin(self)
        self.drawLines(qPainter)
        qPainter.end()
        
    def drawLines(self, qPainter):
      
        pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)

        qPainter.setPen(pen)
        #Draw first frame
        qPainter.drawLine(45, 55, 30, 55)
        qPainter.drawLine(30, 55, 30, 360)
        qPainter.drawLine(30, 360, 730, 360)
        qPainter.drawLine(400, 360, 400, 55)
        qPainter.drawLine(400, 55, 130, 55)
        
        #Draw second frame
        qPainter.drawLine(445, 55, 400, 55)
        qPainter.drawLine(730, 360, 730, 55)
        qPainter.drawLine(730, 55, 610, 55)

    
    def runMain(self):
        
        #Create instance of standby          
        self.startup = Startup()  
        
        #Initialize the serial port and return the connection variable and status
        self.serialStatus, self.serialConnection = self.startup.initSerial()
        
        #Get first day, first sec and emission coefficient
        #self.things is an array.
        self.things = self.startup.sendReceive()
        self.firstDay = self.things[0]
        self.firstSec = self.things[1]
        self.emCoeffS = self.things[2]
        
        #Create an instane of the button class
        self.buttons = Buttons()
        #Pass on the serial connection
        self.buttons.buttonSerial = self.serialConnection
        
        #Pass the first day, first second and emission coefficient to buttons
        self.buttons.firstDay = self.firstDay    
        self.buttons.firstSec = self.firstSec
        self.buttons.emCoeff = self.emCoeffS
        #Print Emission Coefficient to GUI
        self.buttons.printEmCoeff(self.buttons.emCoeff)
          
        
        #Print serial status to statusbar for 5 seconds
        self.statusBar().showMessage(self.serialStatus, 5000)
        
        
        #Set the central widget (Put buttons in window)
        self.setCentralWidget(self.buttons)
        
        
     
    #Question box for quitting the program
    def closeEvent(self, event):
            
        reply = QtGui.QMessageBox.question(self, 
        'Confirm Exit', 
        'Are you sure you want to quit?', 
        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            
        if (reply == QtGui.QMessageBox.Yes):
            event.accept()
                
        else:
            event.ignore()
            
    #Close window when "ESC" is pressed
    def keyPressEvent(self, e):
        
        if e.key() == QtCore.Qt.Key_Escape:
            #Close serial port. Consequences?
            self.serialConnection.close()
            self.close()
    
        
#Class for creating all the buttons. Contains methods for when a button is pressed.
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
        #Array of climate data (Not used yet)
        self.climateDataM = None
        #IR-Emission Coefficient [0.1;1.0]
        self.emCoeff = None
        #Initiate buttons
        self.initButtons()
        #Flag for data
        self.isData = False
      
        
    #Make the buttons
    def initButtons(self):
        #Variables for layout        
        self.top = 50
        self.clmPos = 50
        self.logPos = 450
        
        #Label
        self.plotLabel = QtGui.QLabel("<b>Climate Data</b>", self)
        self.plotLabel.move(self.clmPos, self.top)
        #Label
        self.dateLabel = QtGui.QLabel("<b>Choose a time interval (in days) to plot/save climate data</b>", self)
        self.dateLabel.move(self.clmPos, self.top + 30)

        self.fDayLabel = QtGui.QLabel("Start: <i>None chosen</i>", self)
        self.fDayLabel.move(self.clmPos, self.top + 50) 
        
        
        self.fDayButton = QtGui.QPushButton("Change Start", self)
        self.fDayButton.clicked.connect(self.changeDay)
        self.fDayButton.move(self.clmPos + 175, self.top + 50)
        self.fDayButton.resize(80, 20)
        
        self.lDayLabel = QtGui.QLabel("End:  <i>None chosen</i>", self)
        self.lDayLabel.move(self.clmPos, self.top + 75)
        
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
        self.pbar.setCancelButton(None)
        self.pbar.setWindowTitle("Loading...")
        self.pbar.setLabelText("Loading data from the Arduino and SD-card. \nThis may take several minutes.\n\
        The program will be frozen while loading.")
        
       
        #Button for saving chosen data
        self.saveData_B = QtGui.QPushButton("Save Climate Data", self)
        self.saveData_B.resize(100, 30)
        self.saveData_B.move(self.clmPos + 90, self.top + 175)
        self.saveData_B.clicked.connect(self.saveData_B_Pressed)
        
        
        #Title (needs frame preferably)
        self.logLabel = QtGui.QLabel("<b> Data Logging for IR sensor </b>", self)
        self.logLabel.move(self.logPos, self.top)
        
        
        #Before running a data logging
        self.timeLabel = QtGui.QLabel("<b>Choose logging time</b>", self)
        self.timeLabel.move(self.logPos, self.top + 35)
        
        #Set logging time with button
        self.timeChosen_L = QtGui.QLabel("The logging time is: 0 seconds                          \
                       ", self)
        self.timeChosen_L.move(self.logPos, self.top + 60)
        
        #Button for changing the logging tim value
        self.chaTime_B = QtGui.QPushButton("Change", self)
        self.chaTime_B.resize(80, 30)
        self.chaTime_B.clicked.connect(self.changeTime)
        self.chaTime_B.move(self.logPos, self.top + 80)   
        
        #Combobox to select units
        self.unitBox = QtGui.QComboBox(self)
        self.unitBox.addItem("Seconds")
        self.unitBox.addItem("Minutes")
        self.unitBox.move(self.logPos + 80, self.top + 82)
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
        
        
    def printEmCoeff(self, emCoefficient):
        self.emCoeff_L.setText("The emission factor is: " + str(emCoefficient) + "   ")

    #Function for loading SD-card date into a 
    # list/matrix called self.climateDataM.
    def loadData_B_Pressed(self):
        
        #Check if input is invalid
        if (self.checkUserInput() == "Failure"):
            return        
        
        #Pass the first data point and number of data points
        firstData, nData = self.checkUserInput()
        
        #Make a statusbar showing progress
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(nData)
        self.pbar.show()
        self.pbar.setValue(0)
        
        loadConnect = self.buttonSerial        
                
        
        
        #Clear list/Matrix from last time
        self.climateDataM = np.empty
        #Allocate array (nRows, nColumns)
        self.climateDataM = np.zeros((nData, 9), float)
        
        
        #Clear input buffer if any
        loadConnect.flushInput()
        loadConnect.write("ClimateHistory\n")
        loadConnect.write(str(firstData)+"\n")
        loadConnect.write(str(nData)+"\n")
        
        nCounts = 0
                
        #Load data until stop signal
        while True:
            #Wait for data
            while loadConnect.inWaiting() == 0:
                pass
            
            #Arduino sends: Temp, H, P, Day, Sec 
            #Read line
            line = str(loadConnect.readline())
            
            #Check for stop-signal
            if ("Stop" in line or nCounts == nData):
                break
            
            
            #Split line
            lineArray = line.split(' , ')
            
            #Skip failed measurements (T>900 C), should be done by the Arduino            
            if float(lineArray[0]) > 100:
                continue
                
            #For first point get the day and second
            if (nCounts is 0):
                initDay = int(line.split(' , ')[3])
                initSec = int(line.split(' , ')[4])
                
                
            #Add array indices for days, hours and minutes and secs from start
            lineArray.append(0)
            lineArray.append(0)
            lineArray.append(0)
            lineArray.append(0)
            
            #Convert strings to float
            lineArray = map(float, lineArray)
            
            #Convert days lineArray[3] and seconds lineArray[4]
            # to date and time in [3][4][5][6][7][8]
            #Save current date
            curDay = lineArray[3]
            curDate = date(2014,12,31) + timedelta(days=lineArray[3])
            
            #Get time for at point
            curSec = lineArray[4]
            m,s=divmod(curSec,60)
            h,m=divmod(m,60)
            lineArray[3] = int(curDate.year)
            lineArray[4] = int(curDate.month)
            lineArray[5] = int(curDate.day)
            lineArray[6] = int(h)
            lineArray[7] = int(m)
            lineArray[8] = int((curDay-initDay)*86400 + (curSec - initSec))
            
            #Write the line of data into the climatedata matrix
            self.climateDataM[nCounts] = lineArray
            
            #Increment number of points
            nCounts += 1
            #Update progress bar
            self.pbar.setValue(nCounts)
        
        
        #Remove allocated zeros from matrix
        self.climateDataM = self.climateDataM[0:nCounts]
        
        #Set the progress bar to 100 % and close it
        self.pbar.setValue(nData)
        time.sleep(0.4)
        self.pbar.close()
        
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
    def showClimate_B_Pressed(self):
        
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
        
        #Get length of matrix to find the last parameter
        lengthM = len(self.climateDataM) - 1
        
        #First date of the datapoints
        sDate = date(int(self.climateDataM[0, 3]), int(self.climateDataM[0, 4]), int(self.climateDataM[0, 5]))
        #Last date of the datapoints
        lDate = date(int(self.climateDataM[lengthM, 3]),\
        int(self.climateDataM[lengthM, 4]), int(self.climateDataM[lengthM,5]))
        #Mid date of the datapoints
        mDate =  sDate + timedelta(days=(lDate - sDate).days/2)
        
        #Find first data point in seconds for the day in the middle
        mDeltaSecs = (mDate - sDate).days*(24*3600)

        
        
        
        
        
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
        
        plt.xticks([0, mDeltaSecs,int(self.climateDataM[lengthM, 8])], [str(sDate), str(mDate), str(lDate)], rotation=45)
        plt.tight_layout()
        fig.show()
        
      
    #When 'Change Start' or 'Change End' is pressed    
    def changeDay(self):
        #Check which button is pressed
        sender = self.sender()
        
        while True:
            newDay, ok = QtGui.QInputDialog.getText(self, "Choose a date", "Enter the wanted date in the format: 'dd/mm/yyyy'")
            #Test user input            
            if (ok and len(newDay) is 10 and newDay[2] == "/" and newDay[5] == "/"):
                try:
                    for i in range(0, 10):
                        if i != 2 and i != 5:
                            int(newDay[i])
                            
                except ValueError:
                    print "Please write in the given format"
                    continue
                
                #Check which button was pressed and change text in GUI
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
    #Or send a start measurement and a nr. of measurements for the Arduino.
    def checkUserInput(self):
        
        #Check if dates have been chosen
        if self.startDay is None or self.endDay is None:
            print "Please choose start- and end dates"
            return "Failure"
        
        #Our time starts after 31/12/2014
        startDate = date(2014,12,31)
        
        #Get the start date from the user input string and 
        #convert to days since 31/12/2014
        sDay = int(self.startDay[0:2])
        sMonth = int(self.startDay[3:5])
        sYear  = int(self.startDay[6:10])
        
        sDate = datetime(sYear, sMonth, sDay)
        #Start date in days since 31/12/2014
        deltaStartDays = (sDate.date() - startDate).days
        #Slet
        print "Start date: " + str(deltaStartDays)
        
        #Get the end date from the user input string and 
        #convert to days since 31/12/2014
        eDay = int(self.endDay[0:2])
        eMonth = int(self.endDay[3:5])
        eYear  =int(self.endDay[6:10])
        
        eDate = datetime(eYear, eMonth, eDay)
        #End date in days since 31/12/2014
        deltaEndDays = (eDate.date() - startDate).days
        #Slet
        print "End date: " + str(deltaEndDays)
        
        
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
        #And startDate != endDate?
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
    def start_B_Pressed(self):
       
        #Create a thread for logging
        self.logThread = LogThread()
        #Pass on the serial connection, logging time and emission coefficient
        self.logThread.threadSerial = self.buttonSerial
        self.logThread.logTime = self.logTime
        #Send signal to workThread that it shall emit to makePlot()
        self.connect(self.logThread, QtCore.SIGNAL('startlogging'), self.makePlot)
        #Run the funcion run() in the thread
        self.logThread.start()
        
        self.isData = True
    
    #When the stop button is pressed   
    def stop_B_Pressed(self):
        #Set stop flag in the logging thread
        self.logThread.stopNow = True
        
       
    #Bør (Måske) vise start- og slut klimaparametrer
    def makePlot(self, iRArray,  timeArray):
        
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
        
        if not self.isData:
            print "No temperature data is available, run logging"
            return
        
        #Get the arrays
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
        #Prompt user for emission coefficient and run error handling      
        while True:
            emissionC, ok = QtGui.QInputDialog.getText(self, "Choose emission coefficient",\
            "Enter the emission coefficient of the material (between 0.10 and 1.00).\nPlease turn off the Arduino and start it again before continuing.")
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
         
        clipBoardText = self.getClimate()
        #Make clipboard parameter
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(clipBoardText)
        

  
#Run the program 
def main():
    
    app = QtGui.QApplication(sys.argv)
    climateStation = ClimateStationWindow()
    climateStation.show()
    sys.exit(app.exec_())
    
    
#Run the main function
#__name__ is a class attribute containing the name
if __name__ == "__main__":
    main()
        
        