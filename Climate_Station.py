# -*- coding: utf-8 -*-
"""
This code is written as part of an application for at climate monitor
constisting of an arduino connected to sensors, an SD-card reader and
an LCD-screen and a GUI made by this code. The arduino will have to be
programmed to communicate with the GUI for the monitor to work properly.

The other files required for the program to run are:
Buttons.py
Startup.py
LogThread.py

The program could not have been written if it wasn't for the tutorial on:
http://zetcode.com/gui/pyqt4/
Small parts an pieces have been taken directly from there.

The entire program is run by running this file.
"""
#For the GUI
import sys
from PyQt4 import QtCore, QtGui

#Other parts of the code
from Startup import Startup
from Buttons import Buttons


#Main class, initiates main window and other objects
class ClimateStationWindow(QtGui.QMainWindow):
    
    def __init__(self):
        #Inherit from QtGui.QMainWindow and initiate
        super(ClimateStationWindow, self).__init__()
        #Array with parameters from Startup()
        self.things = None
        #Day and second of first data point
        self.firstDay = None
        self.firstSec = None
        #Emission factor
        self.emCoeffS = None
        self.serialStatus = None
        self.serialConnection = None
        #Run initialization and main
        self.initUI()
        self.runMain()
    
    #Set window size and title
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
    #Function for drawing frames in main window    
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

    #Main function. Runs startup and passes its parameters
    # to the Button() object.
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
        #Buttons will be running most of the window from here.
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
            #Close serial port.
            self.serialConnection.close()
            #Close the program
            self.close()
    
    
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
        
        