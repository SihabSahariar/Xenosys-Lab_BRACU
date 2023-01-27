# Developed By Xenosys Lab
'''
Module : options
Responsibilities : Action Triggerd By AI Object Detection  
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
class ai_action(QWidget):
    def __init__(self):
        super(ai_action,self).__init__()
        loadUi("Forms/options.ui",self)
        self.setWindowTitle("AI CCTV Survaillance For Industry 4.0   - Action Dashboard")
        self.btn_save.clicked.connect(self.save)
    def save(self):
    	self.close()
    	
