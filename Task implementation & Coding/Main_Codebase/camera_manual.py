# Developed By Xenosys Lab
'''
Module : camera_manual
Responsibilities : Manually Add Camera to Database  
'''
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from threading import Thread
#import qdarktheme
import os
from db import DataBase
db = DataBase("modules/databases/device_info.db")
class ManualCamera(QWidget):
    def __init__(self):
        super(ManualCamera,self).__init__()
        loadUi("Forms/camera_manual.ui",self)
        self.setWindowTitle("AI CCTV Survaillance For Industry 4.0   - Manual Add")
        self.setWindowIcon(QIcon(":/icon/icon/dome_camera_80px.png")) 
        self.btn_add.clicked.connect(self.add_db)
        self.btn_cancel.clicked.connect(lambda:self.close())
    def add_db(self):
    	DeviceName = self.deviceName.text()
    	AdditionalInfo = self.add_additionalInfo.text()
    	Group      = self.cameraGroup.currentText()
    	LoginType  = self.loginType.currentText()
    	IP         = self.add_ip.text()
    	Port       = self.add_port.text()
    	UserName   = self.add_username.text()
    	Password   = self.add_password.text()
    	Protocol   = self.add_protocol.currentText()
    	print(DeviceName,AdditionalInfo,Group,LoginType,IP,Port,UserName,Password,Protocol)
    	if(DeviceName!="" and AdditionalInfo!="" and Group!= "" and LoginType != ""and IP!=""and Port!=""and UserName!=""and Password!=""and Protocol!=""):
	        db.insert(DeviceName,AdditionalInfo,Group,LoginType,IP,Port,UserName,Password,Protocol)
	        self.msg = QMessageBox()
	        self.msg.setIcon(QtWidgets.QMessageBox.Information)
	        self.msg.setInformativeText('Information Saved!')
	        self.msg.setWindowTitle("Saved")
	        self.msg.exec_()
	        self.close()
    	else:
	        self.msg = QMessageBox()
	        self.msg.setIcon(QtWidgets.QMessageBox.Critical)
	        self.msg.setInformativeText('Invalid Information!')
	        self.msg.setWindowTitle("Error")
	        self.msg.exec_()
	        return
