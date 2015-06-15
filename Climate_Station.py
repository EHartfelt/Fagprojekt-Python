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
import numpy as np
import matplotlib.pyplot as plt
#Other parts of the code
from Startup import *

#A thread for logging, runs simultaneously with the main window
class LogThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.stopNow = False
        self.threadSerial = None
        self.startTime = None
        self.timeNow = None
        self.logTime = 0
        self.start_Thread_Climate = None
        self.end_Thread_Climate = None
        #Number of measured points
        self.n = 0
    
    def run(self):
        
        self.n = 0        
        
        #self.start_Thread_Climate = self.getClimate()    
        
        #Allocate arrays
        self.iRArray = np.zeros(100*self.logTime)     
        self.timeArray = np.zeros(100*self.logTime)
        
        #Write command to Arduino
        self.threadSerial.write("IRStart")
        
        #Wait for response
        while (self.threadSerial.inWaiting == 0):
                pass
                
        #Get starting time
        self.startTime = time.clock()    
        
        #Run the logging
        while True:
            
            while (self.threadSerial.inWaiting == 0):
                pass
            
            #Calculate the time
            self.timeNow = time.clock() - self.startTime
           
            #Stop after chosen time has passed
            if (self.timeNow >= self.logTime or self.stopNow):
                self.threadSerial.write("IRStop")
                #self.end_Thread_Climate = self.getClimate()
                break
            
            #Get IR value
            self.line = self.threadSerial.readline()
            self.value = float(self.line)
            
            #Write to arrays
            self.iRArray[self.n] = self.value
            self.timeArray[self.n] = self.timeNow
            self.n += 1
        
        #Remove empty indices. Go to n because n is incremented one last time
        #before the while loop ends
        self.timeArray = self.timeArray[0:self.n]
        self.iRArray = self.iRArray[0:self.n]
        #Get climate at end
        
        #Emits signal: 1. Receive QtCore.SIGNAL('startlogging'), then send iRArray and timeArray
        self.emit(QtCore.SIGNAL('startlogging'), self.iRArray, self.timeArray)
        
        #print self.iRArray
        return     
    
    #Send message to the Arduino to pass on the current climate parameters.   
    def getClimate(self):
        
        self.arConnect = self.threadSerial
        self.arConnect.write("CopyClimate")
        time.sleep(0.1)
        #Read temperature, humidity and pressure.
        #Convert to floats to get rid of \n and then to strings.
        self.lineTemp = str(round(float(self.arConnect.readline()), 1))
        self.lineHum = str(float(self.arConnect.readline()))
        self.lineP = str(float(self.arConnect.readline()))
        #Get the current time
        self.timeNow = time.strftime("%d/%m-%Y, %H:%M:%S")
        
        self.climateText = "Temperature: " + self.lineTemp + " C , Humidity: " + self.lineHum \
        + " % , Pressure: " + self.lineP + " mb" + " ; Time: " + self.timeNow
        
        return self.climateText
        
        

#Main class, initiates main window and other objects
class ClimateStationWindow(QtGui.QMainWindow):
    
    def __init__(self):
        #Inherit from QtGui.QMainWindow and initiate
        super(ClimateStationWindow, self).__init__()
        self.things = None
        self.firstDay = ""
        self.firstSec = ""
        self.serialStatus = None
        self.serialConnection = None
        self.runMain()
        
   
    
    def runMain(self):
        
        #Create instance of standby          
        self.startup = Startup()  
        #Initialize the serial port and return the connection variable and status
        self.things = self.startup.initSerial()
        #Send time to the Arduino at startup,  only runs once pr. startup
        self.firstDay, self.firstSec = self.startup.sendReceiveTime() 
        #Might be better as a signal event
        self.serialStatus = self.things[0]
        self.serialConnection = self.things[1]
        
        #Print serial status to statusbar for 5 seconds
        self.statusBar().showMessage(self.serialStatus, 5000)
        
        #Create an instane of the button class
        self.buttons = Buttons()
        #Pass on the serial connection
        self.buttons.buttonSerial = self.serialConnection
        #Pass time for the first measurement to the Buttons object as list appendix
        self.buttons.firstDay = self.firstDay
        self.buttons.firstSec = self.firstSec
        
        #Set the central widget (Put buttons in window)
        self.setCentralWidget(self.buttons)
        
        #Window geometry
        self.setGeometry(100, 75, 750, 400)
        self.setWindowTitle("Climate Station Monitor")
        
        #Lock the window size
        self.setMinimumSize(750, 400)
        self.setMaximumSize(750, 400)
        
     
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
            self.close()


#Class for creating all the buttons. Contains methods for when a button is pressed.
class Buttons(QtGui.QWidget):
    #Constructor
    def __init__(self):
        super(Buttons, self).__init__()
        #Initiate buttons
        self.initButtons()
        #The logging time i set to 0
        self.logTime = 0
        #Serial connection
        self.buttonSerial = None
        #Combobox is set to seconds
        self.comboState = "Seconds"
        #Start and end climate for running measurements
        self.start_Climate = ""
        self.end_Climate = ""
        #First day and first sec sent from Arduino
        self.firstDay = ""
        self.firstSec = ""
        #Start and end day chosen by user
        self.startDay = None
        self.endDay = None
        #Array of climate data (Not used yet)
        self.climateData = None
        
        
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
        
        
        #Button for plotting climate
        self.showClimate_B = QtGui.QPushButton("Plot Climate Data", self)
        self.showClimate_B.resize(90, 30)
        self.showClimate_B.move(self.clmPos, self.top + 125)
        self.showClimate_B.clicked.connect(self.showClimate_B_Pressed)
        #Button for saving chosen data
        self.saveData_B = QtGui.QPushButton("Save Climate Data", self)
        self.saveData_B.resize(100, 30)
        self.saveData_B.move(self.clmPos + 90, self.top + 125)
        #self.showClimate_B.clicked.connect()
        
        
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
        
        
        #Button for copying climate parameters
        self.copyClimate_B = QtGui.QPushButton("Copy Climate Parameters to Clipboard", self)
        self.copyClimate_B.minimumSizeHint
        self.copyClimate_B.move(self.logPos - 150, self.top + 250)
        self.copyClimate_B.clicked.connect(self.copyClimate)
        
    def showClimate_B_Pressed(self):
        #Bør omregne startDay og startSec til et start målepunkt og et antal målepunkter
        #Bør vise en progress bar, der kan 'Cancel'es hvis brugeren ikke gider vente mere
        #Bør sandsynligvis laves i en thread så man kan trykke 'Cancel'
        return
        
    
    #When 'Change Start' or 'Change End' is pressed
    #Bør også tjekke om start er efter slut og om start er før det første målepunkt, hvor den skriver hvis det ikke er
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
                
                #Check which button was pressed
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
            
            
                
            
    
    
    #Function for when user changes the state of the unit combobox
    def onActivated(self):
        if self.comboState is "Seconds":
            self.comboState = "Minutes"
        else:
            self.comboState = "Seconds"
    
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
        
                if self.comboState is "Seconds":
                    self.timeChosen_L.setText("The logging time is: " + str(timeC) + " seconds")
                    #Set logTime to seconds
                    self.logTime = timeC
                    break
            
                elif self.comboState is "Minutes":
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
        #Pass on the serial connection and logging time
        self.logThread.threadSerial = self.buttonSerial
        self.logThread.logTime = self.logTime
        #Send signal to workThread that it shall emit to makePlot()
        self.connect(self.logThread, QtCore.SIGNAL('startlogging'), self.makePlot)
        #Run the funcion run() in the thread
        self.logThread.start()
    
    #When the stop button is pressed   
    def stop_B_Pressed(self):
        #Set stop flag in the logging thread
        self.logThread.stopNow = True
        
       
    #Bør vise start- og slut klimaparametrer
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
        iRArray = self.logThread.iRArray
        timeArray = self.logThread.timeArray

        atStart = self.logThread.start_Thread_Climate
        atEnd = self.logThread.end_Thread_Climate        
        theHeader = str(atStart) + "\n" + str(atEnd)
        
        length = len(timeArray) 
        iRMatrix = np.array([timeArray[1:length], iRArray[1:length]])
        iRMatrix = np.transpose(iRMatrix)
        
        #Get file-name
        filename, ok = QtGui.QInputDialog.getText(self, "File name", "Choose a file name e. g. 'MyFile'")
        #Insert climate parameters in header
        if ok:
            np.savetxt(str(filename)+".txt", iRMatrix, fmt = "%.2f", delimiter = " ", header = theHeader)
        
        
    #Send message to the Arduino to pass on the current climate parameters.   
    def getClimate(self):
        
        arConnect = self.buttonSerial
        arConnect.write("CopyClimate")
        time.sleep(0.1)
        #Read temperature, humidity and pressure.
        #Convert to floats to get rid of \n and then to strings.
        lineTemp = str(round(float(self.arConnect.readline()), 1))
        lineHum = str(float(self.arConnect.readline()))
        lineP = str(float(self.arConnect.readline()))
        #Get the current time
        timeNow = time.strftime("%d/%m-%Y, %H:%M:%S")
        
        climateText = "Temperature: " + lineTemp + " C , Humidity: " + lineHum \
        + " % , Pressure: " + lineP + " mb" + " ; Time: " + timeNow
        
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
       
        
        