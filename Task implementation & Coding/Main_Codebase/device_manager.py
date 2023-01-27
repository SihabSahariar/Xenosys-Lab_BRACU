# Developed By Xenosys Lab
'''
Module : device_manager
Responsibilities : Managing Camera device information and AI configuration also  
'''
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from threading import Thread
import graphics.resource
import os
from db import DataBase
from PyQt5 import QtCore, QtGui, QtWidgets
from camera_manual import *
import home_
from modules.draw_slots import draw
from camera_links import cameraConnect 
from config import settings
class Device_Manager(QWidget):
    def __init__(self):
        super(Device_Manager, self).__init__()
        loadUi("Forms/device_manager.ui",self)
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('modules/databases/device_info.db')     
        self.model = QSqlTableModel()
        self.delrow = -1       
        self.setWindowTitle("AI CCTV Survaillance For Industry 4.0 - Device Manager") 
        self.btn_home.clicked.connect(self.ShowHome)
        self.btn_manual.clicked.connect(self.add_db)
        self.btn_refresh.clicked.connect(self.populate)
        self.btn_delete.clicked.connect(self.delete) 
        self.slot_1.clicked.connect(self.slot1_draw)
        self.slot_2.clicked.connect(self.slot2_draw)
        self.slot_3.clicked.connect(self.slot3_draw)
        self.slot_4.clicked.connect(self.slot4_draw)
        self.slot_5.clicked.connect(self.slot5_draw) 
        self.slot_6.clicked.connect(self.slot6_draw)   

        self.reset1.clicked.connect(self.slot1_remove) 
        self.reset2.clicked.connect(self.slot1_remove) 
        self.reset3.clicked.connect(self.slot1_remove) 
        self.reset4.clicked.connect(self.slot1_remove) 
        self.reset5.clicked.connect(self.slot1_remove) 
        self.reset6.clicked.connect(self.slot1_remove) 
        self.save_thresh.clicked.connect(self.save_config)
        self.save_skip.clicked.connect(self.saveskip)
        self.btn_about.clicked.connect(self.about)
        self.populate()
    def about(self):
        QMessageBox.information(self,"About" ,"Developed By : Xenosys Lab \nTeam Members : Sihab Sahariar, Sami Sadat, Riead Hasan Khan")
    def ShowHome(self):
        self.ui = home_.Home()
        self.ui.show()
        self.close()
    def add_db(self):
        self.x = ManualCamera()
        self.x.show()
        self.populate()
    def populate(self):
        x = settings().getThresh()
        self.thresh.setText(x)
        y = settings().getSkip()
        self.skip.setText(y)        
        self.initializeModel(self.model)
        self.online_total.setText(str(self.model.rowCount()))
        self.AddedCamera.setModel(self.model)
        self.AddedCamera.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.AddedCamera.clicked.connect(self.findrow)
        self.OnlineDeviceList.setModel(self.model)
        self.OnlineDeviceList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cam_links = cameraConnect().LoadCam()
             
    def delete(self):
    	self.model.removeRow(self.AddedCamera.currentIndex().row())
    	self.populate()
    def initializeModel(self,model):
    	self.HEADER = ["ID", "Device Name", "Additional Information", "Camera Group","Login Type", "IP", "Port","User Name","Password","Protocol"]         
    	self.model.setTable('data')
    	self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
    	self.model.select()
    	for i in range(len(self.HEADER)):
    	    self.model.setHeaderData(i,Qt.Horizontal,self.HEADER[i])

    def addrow(self):
    	ret = self.model.insertRows(self.model.rowCount(), 1)
    def findrow(self,i):
    	self.delrow = i.row()
    def save_config(self):
        x = settings().saveThresh(self.thresh.text())
    def saveskip(self):
        x = settings().saveSkip(self.skip.text())


    def slot1_draw(self):
        self.populate()
        try:
            x = draw(cam_link=self.cam_links[0],pickle_file = '0')
            x.slot_akao()
        except:
            QMessageBox.critical(self, "Camera Error", "This camera is not connected")
    def slot2_draw(self):
        self.populate()
        try:
            x = draw(cam_link=self.cam_links[1],pickle_file = '1')
            x.slot_akao()
        except:
            QMessageBox.critical(self, "Camera Error", "This camera is not connected")
    def slot3_draw(self):
        self.populate()
        try:
            x = draw(cam_link=self.cam_links[2],pickle_file = '2')
            x.slot_akao()
        except:
            QMessageBox.critical(self, "Camera Error", "This camera is not connected")
    def slot4_draw(self):
        self.populate()
        try:
            x = draw(cam_link=self.cam_links[3],pickle_file = '3')
            x.slot_akao()
        except:
            QMessageBox.critical(self, "Camera Error", "This camera is not connected")
    def slot5_draw(self):
        self.populate()
        try:
            x = draw(cam_link=self.cam_links[4],pickle_file = '4')
            x.slot_akao()
        except:
            QMessageBox.critical(self, "Camera Error", "This camera is not connected")
    def slot6_draw(self):
        self.populate()
        try:
            x = draw(cam_link=self.cam_links[5],pickle_file = '5')
            x.slot_akao()
        except:
            QMessageBox.critical(self, "Camera Error", "This camera is not connected")


    def slot1_remove(self):
        try:
            os.remove('modules/parking/0')    	
            QMessageBox.information(self, "Slot1 Reset", "Slot1 have been reset!")
        except:
            QMessageBox.critical(self, "Error", "Couldn't Reset")
    def slot2_remove(self):
        try:
            os.remove('modules/parking/1')    	
            QMessageBox.information(self, "Slot2 Reset", "Slot2 have been reset!")
        except:
            QMessageBox.critical(self, "Error", "Couldn't Reset")
    def slot3_remove(self):
        try:
            os.remove('modules/parking/2')    	
            QMessageBox.information(self, "Slot2 Reset", "Slot2 have been reset!")
        except:
            QMessageBox.critical(self, "Error", "Couldn't Reset")

    def slot4_remove(self):
        try:
            os.remove('modules/parking/3')    	
            QMessageBox.information(self, "Slot3 Reset", "Slot3 have been reset!")
        except:
            QMessageBox.critical(self, "Error", "Couldn't Reset")

    def slot5_remove(self):
        try:
            os.remove('modules/parking/4')    	
            QMessageBox.information(self, "Slot4 Reset", "Slot4 have been reset!")
        except:
            QMessageBox.critical(self, "Error", "Couldn't Reset")

    def slot6_remove(self):
        try:
            os.remove('modules/parking/5')    	
            QMessageBox.information(self, "Slot5 Reset", "Slot5 have been reset!")
        except:
            QMessageBox.critical(self, "Error", "Couldn't Reset")

if __name__ == "__main__":
     app = QApplication(sys.argv)
     window = Device_Manager()
     window.show()
     app.exec_()

