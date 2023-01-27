# Developed By Xenosys Lab
'''
Module : live_View
Responsibilities : Streaming Video(Raw/Analytics) and showing those in a grid  
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
from threading import Lock
import numpy as np
import time
import cv2
import os
import threading
from threading import Thread
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
from modules.newwindow import *
import modules.thread 
from modules.detect_face import detectFace
from modules.detect_parkingspace import detectparking
from modules.status import *
from camera_links import cameraConnect 
from Forms import resource
import home_
import psutil
from db import DataBase
import multiprocessing
import subprocess
from datetime import datetime
import signal

db = DataBase("modules/databases/device_info.db")

class VideoStreamWidget(object):  #Record Functionalities
    def __init__(self, cam_link,index):
        self.folder = f"CAM_{index}"
        self.cam_link = cam_link
        self.path = os.path.expanduser(f'~\\Documents\\{self.folder}')
        print(self.path)
        self.date_now = datetime.now().strftime('%Y%m%d')
        self.output_dir = os.path.join(self.path, 'rtsp_saved', self.date_now)
        os.makedirs(self.output_dir, exist_ok=True)
        self.date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_fpath = os.path.join(self.output_dir, 'saved_{}.avi'.format(self.date_time))
        print(self.output_fpath)
        #self.fourcc = cv2.VideoWriter_fourcc(*'MPEG') 
        self.fourcc = cv2.VideoWriter_fourcc('M','P','E','G')
        self.out = cv2.VideoWriter(self.output_fpath, self.fourcc, 30, (640,480))
        self.capture = cv2.VideoCapture(self.cam_link)
        self.thread = Thread(target=self.update, args=())
        #self.thread.daemon = True
        self.thread.start()        
    def update(self):
        # Read the next frame from the stream in a different thread
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
                self.out.write(self.frame)
    def stop(self):
        try:
            self.thread.stop()
            self.out.release()
            self.capture.release()
            cv2.destroyAllWindows()
            print("Stopped")
            exit(1)
        except:
                pass

def run(cam_url,cam_index):
    video_stream_widget = VideoStreamWidget(int(cam_url),cam_index)

def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    self.clicked.emit()
                    return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

class Live_view(QWidget):
    def __init__(self):
        super(Live_view, self).__init__()
        loadUi("Forms/live_view.ui",self)
        self.setWindowTitle("AI CCTV Survaillance For Industry 4.0 - Live View") 
        self.show()
        self.showMaximized()
        self.btn_stop.setVisible(False)      
        self.cam_links = cameraConnect().LoadCam() #Load Camera From Database
        self.msg = str(db.msg)
        self.actual_cam = []+self.cam_links
        self.count = 0
        #check if it's a webcam
        result = None
        for i in range(len(self.cam_links)):
            link = self.cam_links[i]
            try: 
                result = int(link)
                self.cam_links[i] = result
            except: 
                pass
        self.baki = 64-len(self.cam_links)
        i = 0
        while(i<self.baki):
        	self.cam_links.append("127.0.0.1") # dummy address
        	i+=1      
        self.proc = [None for i in range(len(self.actual_cam))]
        self.actives = [False for i in range(len(self.cam_links))]
        self.labels = []
        self.threads = []
        self.records = []

        col = 4
        row = int(len(self.cam_links)/col) 
    
        self.killThread()

        for index, cam_link in enumerate(self.cam_links):
            try:
                if str(self.cam_links[index])==str(self.actual_cam[index]): # Check Camera if actually connected before start threading
                    th = modules.thread.ThreadVideo(self, cam_link, index)
                    th.imgSignal.connect(self.getImg)
                    self.threads.append(th)
            except:
                    pass

            # Screen ---------------------
            self.lbl_cam = QLabel()
            self.lbl_cam.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.lbl_cam.setFont(QFont("Times", 12))
            self.lbl_cam.setStyleSheet(
                "color: rgb(255,255,255);"
                "background-color: rgb(30,30,30);"
                "qproperty-alignment: AlignCenter;")

            clickable(self.lbl_cam).connect(partial(self.showCam, index)) 
            self.comboBox = QComboBox()  #Analytics er combobox
            self.AI_LIST = ["AI Analytics",
            "Face Detection",
            "Parking Surface",
            "People Counting",            
            "Product Detection",
            "Fire Detection",
            "QR Code Detection",
            "Barcode Detection"]

            for i in self.AI_LIST:
            	self.comboBox.addItem(i)
            self.comboBox.activated.connect(partial(self.selectionChange,index)) # Connect Combo Box With Threading
            self.labels.append(self.lbl_cam)

            try:
                if index == 0:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setMaximumSize(QSize(30, 30))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,0,self.btn1,self.threads[0]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1) 
                    self.layout.addWidget(self.frame,0,0)
                    self.layout.addWidget(self.lbl_cam, 1,0)
                elif index == 1:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,1,self.btn1,self.threads[1]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1) 
                    self.layout.addWidget(self.frame,0,1)
                    self.layout.addWidget(self.lbl_cam, 1,1)
                elif index == 2:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,2,self.btn1,self.threads[2]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,0)
                    self.layout.addWidget(self.lbl_cam, 3,0)
                elif index == 3:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,1)
                    self.layout.addWidget(self.lbl_cam, 3,1) 
      
                elif index == 4:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,0,2)
                    self.layout.addWidget(self.lbl_cam, 1,2) 
                elif index == 5:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1) 
                    self.layout.addWidget(self.frame,0,3)
                    self.layout.addWidget(self.lbl_cam, 1,3)
                elif index == 6:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,2)
                    self.layout.addWidget(self.lbl_cam, 3,2) 
                elif index == 7:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,3) 
                    self.layout.addWidget(self.lbl_cam, 3,3) 

                elif index == 8:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,0)
                    self.layout.addWidget(self.lbl_cam, 5,0) 
                elif index == 9:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,1)
                    self.layout.addWidget(self.lbl_cam, 5,1)
                elif index == 10:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,2) 
                    self.layout.addWidget(self.lbl_cam, 5,2) 
                elif index == 11:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,3) 
                    self.layout.addWidget(self.lbl_cam, 5,3) 

                elif index == 12:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,0) 
                    self.layout.addWidget(self.lbl_cam, 7,0) 
                elif index == 13:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,1) 
                    self.layout.addWidget(self.lbl_cam, 7,1) 
                elif index == 14:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,2) 
                    self.layout.addWidget(self.lbl_cam, 7,2) 
                elif index == 15:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,3) 
                    self.layout.addWidget(self.lbl_cam, 7,3) 

                elif index == 16:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,0,4)
                    self.layout.addWidget(self.lbl_cam, 1,4) 
                elif index == 17:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,0,5)
                    self.layout.addWidget(self.lbl_cam, 1,5)
                elif index == 18:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,0,6)
                    self.layout.addWidget(self.lbl_cam, 1,6)
                elif index == 19:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,0,7)
                    self.layout.addWidget(self.lbl_cam, 1,7) 

                elif index == 20:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,4) 
                    self.layout.addWidget(self.lbl_cam, 3,4)
                elif index == 21:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,5) 
                    self.layout.addWidget(self.lbl_cam, 3,5)
                elif index == 22:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,6) 
                    self.layout.addWidget(self.lbl_cam, 3,6) 
                elif index == 23:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,2,7)
                    self.layout.addWidget(self.lbl_cam, 3,7) 

                elif index == 24:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,4) 
                    self.layout.addWidget(self.lbl_cam, 5,4)
                elif index == 25:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,5) 
                    self.layout.addWidget(self.lbl_cam, 5,5) 
                elif index == 26:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,6) 
                    self.layout.addWidget(self.lbl_cam, 5,6)
                elif index == 27:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,4,7) 
                    self.layout.addWidget(self.lbl_cam, 5,7) 

                elif index == 28:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,4) 
                    self.layout.addWidget(self.lbl_cam, 7,4) 
                elif index == 29:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,5) 
                    self.layout.addWidget(self.lbl_cam, 7,5)
                elif index == 30:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,6) 
                    self.layout.addWidget(self.lbl_cam, 7,6) 
                elif index == 31:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,6,7) 
                    self.layout.addWidget(self.lbl_cam, 7,7) 

                elif index == 32:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,0)
                    self.layout.addWidget(self.lbl_cam, 9,0) 
                elif index == 33:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,1)
                    self.layout.addWidget(self.lbl_cam, 9,1)
                elif index == 34:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,2)
                    self.layout.addWidget(self.lbl_cam, 9,2)
                elif index == 35:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,3)
                    self.layout.addWidget(self.lbl_cam, 9,3) 
                
                elif index == 36:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,4) 
                    self.layout.addWidget(self.lbl_cam, 9,4)
                elif index == 37:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,5) 
                    self.layout.addWidget(self.lbl_cam, 9,5)
                elif index == 38:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,6) 
                    self.layout.addWidget(self.lbl_cam, 9,6) 
                elif index == 39:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,8,7)
                    self.layout.addWidget(self.lbl_cam, 9,7) 

                elif index == 40:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,0) 
                    self.layout.addWidget(self.lbl_cam, 11,0)
                elif index == 41:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,1) 
                    self.layout.addWidget(self.lbl_cam, 11,1) 
                elif index == 42:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,2) 
                    self.layout.addWidget(self.lbl_cam, 11,2)
                elif index == 43:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,3) 
                    self.layout.addWidget(self.lbl_cam, 11,3) 

                elif index == 44:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,4) 
                    self.layout.addWidget(self.lbl_cam, 11,4) 
                elif index == 45:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,5) 
                    self.layout.addWidget(self.lbl_cam, 11,5)
                elif index == 46:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,6) 
                    self.layout.addWidget(self.lbl_cam, 11,6) 
                elif index == 47:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,10,7) 
                    self.layout.addWidget(self.lbl_cam, 11,7) 

                elif index == 48:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,0)
                    self.layout.addWidget(self.lbl_cam, 13,0)
                elif index == 49:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,1)
                    self.layout.addWidget(self.lbl_cam, 13,1) 
                elif index == 50:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,2) 
                    self.layout.addWidget(self.lbl_cam, 13,2)
                elif index == 51:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,3)
                    self.layout.addWidget(self.lbl_cam, 13,3) 
      
                elif index == 52:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,4) 
                    self.layout.addWidget(self.lbl_cam, 13,4) 
                elif index == 53:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,5)
                    self.layout.addWidget(self.lbl_cam, 13,5)
                elif index == 54:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,6) 
                    self.layout.addWidget(self.lbl_cam, 13,6) 
                elif index == 55:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,12,7) 
                    self.layout.addWidget(self.lbl_cam, 13,7) 

                elif index == 56:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,0)
                    self.layout.addWidget(self.lbl_cam, 15,0) 
                elif index == 57:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,1)
                    self.layout.addWidget(self.lbl_cam, 15,1)
                elif index == 58:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,2) 
                    self.layout.addWidget(self.lbl_cam, 15,2) 
                elif index == 59:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,3) 
                    self.layout.addWidget(self.lbl_cam, 15,3) 

                elif index == 60:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,4)
                    self.layout.addWidget(self.lbl_cam, 15,4) 
                elif index == 61:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,5)
                    self.layout.addWidget(self.lbl_cam, 15,5)
                elif index == 62:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,6) 
                    self.layout.addWidget(self.lbl_cam, 15,6) 
                elif index == 63:
                    self.btn1 = QPushButton()
                    self.btn1.setCheckable(True)
                    self.btn1.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
                    self.btn1.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                    if(index<len(self.actual_cam)):
                        self.btn1.clicked.connect(partial(self.recordCamera,index,self.btn1,self.threads[index]))
                    else:
                        self.btn1.clicked.connect(lambda:QMessageBox.critical(self, "Camera Error", "This camera is not connected")  )
                    self.frame = QFrame()
                    self.frame.setMaximumHeight(30)
                    self.h = QHBoxLayout(self.frame)
                    self.h.setContentsMargins(0, 0, 0, 0)
                    self.h.addWidget(self.comboBox)
                    self.h.addWidget(self.btn1)
                    self.layout.addWidget(self.frame,14,7) 
                    self.layout.addWidget(self.lbl_cam, 15,7) 
            except:
                pass

        # Time Screen ----------------
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showSystem)
        self.timer.start(1000)
        self.showSystem()

        # # Timer Auto Restart threads -
        # self.timer_th = QTimer(self)
        # self.timer_th.timeout.connect(self.refreshThread)
        # self.timer_th.start(60) # 60 secs
        # -----------------------------

        self.newWindow = NewWindow(self)
        self.tableStatus = TableStatus(self)
        self.cam8() # By Default 8 Grid

		# Button Functions Integration        
        self.btn_cam1.clicked.connect(self.cam1)
        self.btn_cam_4.clicked.connect(self.cam4)
        self.btn_cam_8.clicked.connect(self.cam8)
        self.btn_cam_16.clicked.connect(self.cam16)
        self.btn_cam_32.clicked.connect(self.cam32)
        self.btn_cam_64.clicked.connect(self.cam64)        
        self.btn_home.clicked.connect(self.ShowHome)
        self.btn_about.clicked.connect(self.about)

        self.process = []

        #Start Raw Video Stream By Default
        self.cam1_raw_start()
        self.cam2_raw_start()
        self.cam3_raw_start()
        self.cam4_raw_start()
        self.cam5_raw_start()
        self.cam6_raw_start()
        self.cam7_raw_start()
        self.cam8_raw_start() 
        self.cam9_raw_start() 
        self.cam10_raw_start()
        self.cam11_raw_start()
        self.cam12_raw_start()     

    def about(self):
    	QMessageBox.information(self,"About" ,"Developed By : Xenosys Lab \nTeam Members : Sihab Sahariar, Sami Sadat, Riead Hasan Khan")

    def selectionChange(self,index,selected_analytics): # Analytics Select
            lst = [selected_analytics,index]
            cam_link = self.cam_links[index]

            if index==0 and selected_analytics==1:
                self.cam1_analytics_start()
            elif index==1 and selected_analytics==2:
                self.cam2_analytics_start()
            elif index==2 and selected_analytics==2:
                self.cam3_analytics_start()
            elif index==3 and selected_analytics==2:
                self.cam4_analytics_start()          
            elif index==4 and selected_analytics==2:
                self.cam5_analytics_start()  
            elif index==5 and selected_analytics==2:
                self.cam6_analytics_start() 
            elif index==6 and selected_analytics==2:
                self.cam7_analytics_start() 
            elif index==7 and selected_analytics==2:
                self.cam8_analytics_start() 
            elif index==8 and selected_analytics==2:
                self.cam9_analytics_start() 
            elif index==9 and selected_analytics==2:
                self.cam10_analytics_start() 
            elif index==10 and selected_analytics==2:
                self.cam11_analytics_start() 
            elif index==11 and selected_analytics==2:
                self.cam12_analytics_start()                                                
            else:
                QMessageBox.information(self, "Analytics", f"Please Select Appropiate Analytics!")  

    def refreshThread(self): 
        self.listView.clear()
        for i in self.actual_cam:
            self.listView.addItem(str(i))        
        for i in self.threads:
            i.threadactive = True
            i.start()

    def killThread(self): 
        for i in self.threads:
            try:
                i.terminate()
                i.stop()
            except:
                pass
        self.listView.clear()
        for i in self.actual_cam:
            self.listView.addItem(str(i))

    def sizeHint(self):
        return QSize(width, height)

    def resizeEvent(self, event):
        self.update()

    @pyqtSlot(np.ndarray, int, bool)
    def getImg(self, img, index, active):
        self.actives[index] = active
        if active:
            self.img = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
            self.labels[index].setPixmap(QPixmap(self.img).scaled(self.labels[index].size(), Qt.KeepAspectRatio, Qt.FastTransformation) )
            if index == self.newWindow.index:
                self.newWindow.lbl_cam.setPixmap(QPixmap.fromImage(self.img))
        else:
            if index == self.newWindow.index:
                self.newWindow.close()

    def showSystem(self): #System Information 
        self.vms = psutil.cpu_percent()
        self.process = psutil.Process(os.getpid())
        self.line_VMS_CPU.setText(str(round(self.vms/psutil.cpu_count(),2))+'%')
        self.line_All_CPU.setText(str(self.vms)+'%')
        self.line_Memory.setText(str(round(self.process.memory_percent(),2))+'%')

        for index, (self.lbl_cam, active) in enumerate(zip(self.labels, self.actives)): # Check if any camera is dead
            if not active:
                text_ = "CAMERA {}\nNOT CONNECTED!".format(index+1) 
                self.lbl_cam.setText(text_)


    def showCam(self, index):
        self.newWindow.index = index
        if not self.actives[index]:
            text_ = "CAMERA {}\nNOT CONNECTED!".format(index+1)
            self.newWindow.lbl_cam.setText(text_)
        self.newWindow.setWindowTitle('CAMERA {}'.format(index+1))
        self.newWindow.resize(1000,600)
        self.newWindow.show()

    def recordCamera(self,index,obj,recObj):  # Record Function - Not Implemented 
        if obj.isChecked(): #Start Recording
            obj.setIcon(QIcon(":/icon/icon/rec_recording.ico"))
            print(index)
            print(self.proc)
            #self.proc[index] = multiprocessing.Process(target=run, args=(self.actual_cam[index],str(index)))
            #self.proc[index].start()
            recObj._record = True
        else: #Stop Recording
            obj.setIcon(QIcon(":/icon/icon/rec_normal.ico"))
            #self.proc[index].terminate()
            #self.proc[index].join()        	
            recObj._record = False

        
             

    def cam1(self):
        try:
            self.layout.itemAt(0).widget().setVisible(True)
            self.layout.itemAt(1).widget().setVisible(True)
        except:
            QMessageBox.critical(self, "Camera Error", "You don't have sufficient camera")            
        try:
            for i in range(2,128):
                self.layout.itemAt(i).widget().setVisible(False)
        except:
            pass
    def cam4(self):
        try:
            self.layout.itemAt(0).widget().setVisible(True)
            self.layout.itemAt(1).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(2).widget().setVisible(True)
            self.layout.itemAt(3).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(4).widget().setVisible(True)
            self.layout.itemAt(5).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(6).widget().setVisible(True)
            self.layout.itemAt(7).widget().setVisible(True)
        except:
            QMessageBox.critical(self, "Camera Error", "You don't have sufficient camera")
        
        try:
            for i in range(8,128):
                self.layout.itemAt(i).widget().setVisible(False)
        except:
            pass
    def cam8(self):
        try:
            self.layout.itemAt(0).widget().setVisible(True)
            self.layout.itemAt(1).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(2).widget().setVisible(True)
            self.layout.itemAt(3).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(4).widget().setVisible(True)
            self.layout.itemAt(5).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(6).widget().setVisible(True)
            self.layout.itemAt(7).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(8).widget().setVisible(True)
            self.layout.itemAt(9).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(10).widget().setVisible(True)
            self.layout.itemAt(11).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(12).widget().setVisible(True)
            self.layout.itemAt(13).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(14).widget().setVisible(True)
            self.layout.itemAt(15).widget().setVisible(True)
        except:
            QMessageBox.critical(self, "Camera Error", "You don't have sufficient camera")

        try:
            for i in range(16,128):
                self.layout.itemAt(i).widget().setVisible(False)
        except:
            pass
    def cam16(self):
        try:
            self.layout.itemAt(0).widget().setVisible(True)
            self.layout.itemAt(1).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(2).widget().setVisible(True)
            self.layout.itemAt(3).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(4).widget().setVisible(True)
            self.layout.itemAt(5).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(6).widget().setVisible(True)
            self.layout.itemAt(7).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(8).widget().setVisible(True)
            self.layout.itemAt(9).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(10).widget().setVisible(True)
            self.layout.itemAt(11).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(12).widget().setVisible(True)
            self.layout.itemAt(13).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(14).widget().setVisible(True)
            self.layout.itemAt(15).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(16).widget().setVisible(True)
            self.layout.itemAt(17).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(18).widget().setVisible(True)
            self.layout.itemAt(19).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(20).widget().setVisible(True)
            self.layout.itemAt(21).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(22).widget().setVisible(True)
            self.layout.itemAt(23).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(24).widget().setVisible(True)
            self.layout.itemAt(25).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(26).widget().setVisible(True)
            self.layout.itemAt(27).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(28).widget().setVisible(True)
            self.layout.itemAt(29).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(30).widget().setVisible(True)
            self.layout.itemAt(31).widget().setVisible(True)
        except:
            QMessageBox.critical(self, "Camera Error", "You don't have sufficient camera")  
        try:
            for i in range(32,128):
                self.layout.itemAt(i).widget().setVisible(False)
        except:
            pass                     
    def cam32(self):
        try:
            self.layout.itemAt(0).widget().setVisible(True)
            self.layout.itemAt(1).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(2).widget().setVisible(True)
            self.layout.itemAt(3).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(4).widget().setVisible(True)
            self.layout.itemAt(5).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(6).widget().setVisible(True)
            self.layout.itemAt(7).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(8).widget().setVisible(True)
            self.layout.itemAt(9).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(10).widget().setVisible(True)
            self.layout.itemAt(11).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(12).widget().setVisible(True)
            self.layout.itemAt(13).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(14).widget().setVisible(True)
            self.layout.itemAt(15).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(16).widget().setVisible(True)
            self.layout.itemAt(17).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(18).widget().setVisible(True)
            self.layout.itemAt(19).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(20).widget().setVisible(True)
            self.layout.itemAt(21).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(22).widget().setVisible(True)
            self.layout.itemAt(23).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(24).widget().setVisible(True)
            self.layout.itemAt(25).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(26).widget().setVisible(True)
            self.layout.itemAt(27).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(28).widget().setVisible(True)
            self.layout.itemAt(29).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(30).widget().setVisible(True)
            self.layout.itemAt(31).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(32).widget().setVisible(True)
            self.layout.itemAt(33).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(34).widget().setVisible(True)
            self.layout.itemAt(35).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(36).widget().setVisible(True)
            self.layout.itemAt(37).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(38).widget().setVisible(True)
            self.layout.itemAt(39).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(40).widget().setVisible(True)
            self.layout.itemAt(41).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(42).widget().setVisible(True)
            self.layout.itemAt(43).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(44).widget().setVisible(True)
            self.layout.itemAt(45).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(46).widget().setVisible(True)
            self.layout.itemAt(47).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(48).widget().setVisible(True)
            self.layout.itemAt(49).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(50).widget().setVisible(True)
            self.layout.itemAt(51).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(52).widget().setVisible(True)
            self.layout.itemAt(53).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(54).widget().setVisible(True)
            self.layout.itemAt(55).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(56).widget().setVisible(True)
            self.layout.itemAt(57).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(58).widget().setVisible(True)
            self.layout.itemAt(59).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(60).widget().setVisible(True)
            self.layout.itemAt(61).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(62).widget().setVisible(True)
            self.layout.itemAt(63).widget().setVisible(True)
        except:
            QMessageBox.critical(self, "Camera Error", "You don't have sufficient camera")   
        try:
            for i in range(64,128):
                self.layout.itemAt(i).widget().setVisible(False)
        except:
            pass               
    def cam64(self):
        try:
            self.layout.itemAt(0).widget().setVisible(True)
            self.layout.itemAt(1).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(2).widget().setVisible(True)
            self.layout.itemAt(3).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(4).widget().setVisible(True)
            self.layout.itemAt(5).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(6).widget().setVisible(True)
            self.layout.itemAt(7).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(8).widget().setVisible(True)
            self.layout.itemAt(9).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(10).widget().setVisible(True)
            self.layout.itemAt(11).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(12).widget().setVisible(True)
            self.layout.itemAt(13).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(14).widget().setVisible(True)
            self.layout.itemAt(15).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(16).widget().setVisible(True)
            self.layout.itemAt(17).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(18).widget().setVisible(True)
            self.layout.itemAt(19).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(20).widget().setVisible(True)
            self.layout.itemAt(21).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(22).widget().setVisible(True)
            self.layout.itemAt(23).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(24).widget().setVisible(True)
            self.layout.itemAt(25).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(26).widget().setVisible(True)
            self.layout.itemAt(27).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(28).widget().setVisible(True)
            self.layout.itemAt(29).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(30).widget().setVisible(True)
            self.layout.itemAt(31).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(32).widget().setVisible(True)
            self.layout.itemAt(33).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(34).widget().setVisible(True)
            self.layout.itemAt(35).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(36).widget().setVisible(True)
            self.layout.itemAt(37).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(38).widget().setVisible(True)
            self.layout.itemAt(39).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(40).widget().setVisible(True)
            self.layout.itemAt(41).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(42).widget().setVisible(True)
            self.layout.itemAt(43).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(44).widget().setVisible(True)
            self.layout.itemAt(45).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(46).widget().setVisible(True)
            self.layout.itemAt(47).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(48).widget().setVisible(True)
            self.layout.itemAt(49).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(50).widget().setVisible(True)
            self.layout.itemAt(51).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(52).widget().setVisible(True)
            self.layout.itemAt(53).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(54).widget().setVisible(True)
            self.layout.itemAt(55).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(56).widget().setVisible(True)
            self.layout.itemAt(57).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(58).widget().setVisible(True)
            self.layout.itemAt(59).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(60).widget().setVisible(True)
            self.layout.itemAt(61).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(62).widget().setVisible(True)
            self.layout.itemAt(63).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(64).widget().setVisible(True)
            self.layout.itemAt(65).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(66).widget().setVisible(True)
            self.layout.itemAt(67).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(68).widget().setVisible(True)
            self.layout.itemAt(69).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(70).widget().setVisible(True)
            self.layout.itemAt(71).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(72).widget().setVisible(True)
            self.layout.itemAt(73).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(74).widget().setVisible(True)
            self.layout.itemAt(75).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(76).widget().setVisible(True)
            self.layout.itemAt(77).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(78).widget().setVisible(True)
            self.layout.itemAt(79).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(80).widget().setVisible(True)
            self.layout.itemAt(81).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(82).widget().setVisible(True)
            self.layout.itemAt(83).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(84).widget().setVisible(True)
            self.layout.itemAt(85).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(86).widget().setVisible(True)
            self.layout.itemAt(87).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(88).widget().setVisible(True)
            self.layout.itemAt(89).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(90).widget().setVisible(True)
            self.layout.itemAt(91).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(92).widget().setVisible(True)
            self.layout.itemAt(93).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(94).widget().setVisible(True)
            self.layout.itemAt(95).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(96).widget().setVisible(True)
            self.layout.itemAt(97).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(98).widget().setVisible(True)
            self.layout.itemAt(99).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(100).widget().setVisible(True)
            self.layout.itemAt(101).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(102).widget().setVisible(True)
            self.layout.itemAt(103).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(104).widget().setVisible(True)
            self.layout.itemAt(105).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(106).widget().setVisible(True)
            self.layout.itemAt(107).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(108).widget().setVisible(True)
            self.layout.itemAt(109).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(110).widget().setVisible(True)
            self.layout.itemAt(111).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(112).widget().setVisible(True)
            self.layout.itemAt(113).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(114).widget().setVisible(True)
            self.layout.itemAt(115).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(116).widget().setVisible(True)
            self.layout.itemAt(117).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(118).widget().setVisible(True)
            self.layout.itemAt(119).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(120).widget().setVisible(True)
            self.layout.itemAt(121).widget().setVisible(True) 
        except:
            pass
        try:       
            self.layout.itemAt(122).widget().setVisible(True)
            self.layout.itemAt(123).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(124).widget().setVisible(True)
            self.layout.itemAt(125).widget().setVisible(True)
        except:
            pass
        try:
            self.layout.itemAt(126).widget().setVisible(True)
            self.layout.itemAt(127).widget().setVisible(True)
        except:
            QMessageBox.critical(self, "Camera Error", "You don't have sufficient camera")   

    def ShowHome(self): 
    	# Kill All Raw/Analytics Feed 
        try:
            self.cam1_raw_stop()
            self.cam1_analytics_stop()
            self.cam2_raw_stop()
            self.cam2_analytics_stop()
            self.cam3_raw_stop()
            self.cam3_analytics_stop()
            self.cam4_raw_stop()
            self.cam4_analytics_stop()
            self.cam5_raw_stop()
            self.cam5_analytics_stop()
            self.cam6_raw_stop()
            self.cam6_analytics_stop()
        except:
            pass
        try:
            self.x = home_.Home()
            self.x.show()
        except:
            pass
        self.close()

#-----------------------------------------------------------------------------------------------------------
#---------------------------------CAMERA ANALYSIS FOOTAGE THROUGH THREADING--------------------
#-----------------------------------------------------------------------------------------------------------

#------------------------------------CAM-1-----------------------------------
    def cam1_raw_start(self): 
        self.cam1_raw = modules.thread.ThreadVideo(self,self.cam_links[0], 0)
        self.cam1_raw.imgSignal.connect(self.getImg)
        self.cam1_raw.start()
    def cam1_analytics_start(self): 
        try:
            self.cam1_raw_stop()
            print("Stopped")
        except:
            pass
        self.cam1_analytics = modules.detect_face.detectFace(self,self.cam_links[0], 0) #detectface
        #self.cam1_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[0], 0) #detectparking        
        self.cam1_analytics.imgSignal.connect(self.getImg)
        self.cam1_analytics.start() 
    def cam1_raw_stop(self): 
        self.cam1_raw.stop()
    def cam1_analytics_stop(self): 
        self.cam1_analytics.stop()

#------------------------------------CAM-2-----------------------------------
    def cam2_raw_start(self): 
        self.cam2_raw = modules.thread.ThreadVideo(self,self.cam_links[1], 1)
        self.cam2_raw.imgSignal.connect(self.getImg)
        self.cam2_raw.start()
    def cam2_analytics_start(self): 
        try:
            self.cam2_raw_stop()
        except:
            pass
        self.cam2_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[1], 1)
        self.cam2_analytics.imgSignal.connect(self.getImg)
        self.cam2_analytics.start() 
    def cam2_raw_stop(self): 
        self.cam2_raw.stop()
    def cam2_analytics_stop(self): 
        self.cam2_analytics.stop()

#------------------------------------CAM-3-----------------------------------
    def cam3_raw_start(self): 
        self.cam3_raw = modules.thread.ThreadVideo(self,self.cam_links[2], 2)
        self.cam3_raw.imgSignal.connect(self.getImg)
        self.cam3_raw.start()
    def cam3_analytics_start(self): 
        try:
            self.cam3_raw_stop()
        except:
            pass
        self.cam3_analytics =modules.detect_parkingspace.detectparking(self,self.cam_links[2], 2)
        self.cam3_analytics.imgSignal.connect(self.getImg)
        self.cam3_analytics.start() 
    def cam3_raw_stop(self): 
        self.cam3_raw.stop()
    def cam3_analytics_stop(self): 
        self.cam3_analytics.stop()
#------------------------------------CAM-4-----------------------------------
    def cam4_raw_start(self): 
        self.cam4_raw = modules.thread.ThreadVideo(self,self.cam_links[3], 3)
        self.cam4_raw.imgSignal.connect(self.getImg)
        self.cam4_raw.start()
    def cam4_analytics_start(self): 
        try:
            self.cam4_raw_stop()
        except:
            pass
        self.cam4_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[3], 3)
        self.cam4_analytics.imgSignal.connect(self.getImg)
        self.cam4_analytics.start() 
    def cam4_raw_stop(self): 
        self.cam4_raw.stop()
    def cam4_analytics_stop(self): 
        self.cam4_analytics.stop()

#------------------------------------CAM-5-----------------------------------
    def cam5_raw_start(self): 
        self.cam5_raw = modules.thread.ThreadVideo(self,self.cam_links[4], 4)
        self.cam5_raw.imgSignal.connect(self.getImg)
        self.cam5_raw.start()
    def cam5_analytics_start(self): 
        try:
            self.cam5_raw_stop()
        except:
            pass
        self.cam5_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[4], 4)
        self.cam5_analytics.imgSignal.connect(self.getImg)
        self.cam5_analytics.start() 
    def cam5_raw_stop(self): 
        self.cam5_raw.stop()
    def cam5_analytics_stop(self): 
        self.cam5_analytics.stop()
#------------------------------------CAM-6-----------------------------------
    def cam6_raw_start(self): 
        self.cam6_raw = modules.thread.ThreadVideo(self,self.cam_links[5], 5)
        self.cam6_raw.imgSignal.connect(self.getImg)
        self.cam6_raw.start()
    def cam6_analytics_start(self): 
        try:
            self.cam6_raw_stop()
        except:
            pass
        self.cam6_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[5], 5)
        self.cam6_analytics.imgSignal.connect(self.getImg)
        self.cam6_analytics.start() 
    def cam6_raw_stop(self): 
        self.cam6_raw.stop()
    def cam6_analytics_stop(self): 
        self.cam6_analytics.stop()

#------------------------------------CAM-7-----------------------------------
    def cam7_raw_start(self): 
        self.cam7_raw = modules.thread.ThreadVideo(self,self.cam_links[6], 6)
        self.cam7_raw.imgSignal.connect(self.getImg)
        self.cam7_raw.start()
    def cam7_analytics_start(self): 
        try:
            self.cam7_raw_stop()
        except:
            pass
        self.cam7_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[6], 6)
        self.cam7_analytics.imgSignal.connect(self.getImg)
        self.cam7_analytics.start() 
    def cam7_raw_stop(self): 
        self.cam7_raw.stop()
    def cam7_analytics_stop(self): 
        self.cam7_analytics.stop()

#------------------------------------CAM-8-----------------------------------
    def cam8_raw_start(self): 
        self.cam8_raw = modules.thread.ThreadVideo(self,self.cam_links[7], 7)
        self.cam8_raw.imgSignal.connect(self.getImg)
        self.cam8_raw.start()
    def cam8_analytics_start(self): 
        try:
            self.cam8_raw_stop()
        except:
            pass
        self.cam8_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[7], 7)
        self.cam8_analytics.imgSignal.connect(self.getImg)
        self.cam8_analytics.start() 
    def cam8_raw_stop(self): 
        self.cam8_raw.stop()
    def cam8_analytics_stop(self): 
        self.cam8_analytics.stop()

#------------------------------------CAM-9-----------------------------------
    def cam9_raw_start(self): 
        self.cam9_raw = modules.thread.ThreadVideo(self,self.cam_links[8], 8)
        self.cam9_raw.imgSignal.connect(self.getImg)
        self.cam9_raw.start()
    def cam9_analytics_start(self): 
        try:
            self.cam9_raw_stop()
        except:
            pass
        self.cam9_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[8], 8)
        self.cam9_analytics.imgSignal.connect(self.getImg)
        self.cam9_analytics.start() 
    def cam9_raw_stop(self): 
        self.cam9_raw.stop()
    def cam9_analytics_stop(self): 
        self.cam9_analytics.stop()


#------------------------------------CAM-10-----------------------------------
    def cam10_raw_start(self): 
        self.cam10_raw = modules.thread.ThreadVideo(self,self.cam_links[9], 9)
        self.cam10_raw.imgSignal.connect(self.getImg)
        self.cam10_raw.start()
    def cam10_analytics_start(self): 
        try:
            self.cam10_raw_stop()
        except:
            pass
        self.cam10_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[9], 9)
        self.cam10_analytics.imgSignal.connect(self.getImg)
        self.cam10_analytics.start() 
    def cam10_raw_stop(self): 
        self.cam10_raw.stop()
    def cam10_analytics_stop(self): 
        self.cam10_analytics.stop()
#------------------------------------CAM-11-----------------------------------
    def cam11_raw_start(self): 
        self.cam11_raw = modules.thread.ThreadVideo(self,self.cam_links[10], 10)
        self.cam11_raw.imgSignal.connect(self.getImg)
        self.cam11_raw.start()
    def cam11_analytics_start(self): 
        try:
            self.cam11_raw_stop()
        except:
            pass
        self.cam11_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[10], 10)
        self.cam11_analytics.imgSignal.connect(self.getImg)
        self.cam11_analytics.start() 
    def cam11_raw_stop(self): 
        self.cam11_raw.stop()
    def cam11_analytics_stop(self): 
        self.cam11_analytics.stop()

#------------------------------------CAM-12-----------------------------------
    def cam12_raw_start(self): 
        self.cam12_raw = modules.thread.ThreadVideo(self,self.cam_links[11], 11)
        self.cam12_raw.imgSignal.connect(self.getImg)
        self.cam12_raw.start()
    def cam12_analytics_start(self): 
        try:
            self.cam12_raw_stop()
        except:
            pass
        self.cam12_analytics = modules.detect_parkingspace.detectparking(self,self.cam_links[11], 11)
        self.cam12_analytics.imgSignal.connect(self.getImg)
        self.cam12_analytics.start() 
    def cam12_raw_stop(self): 
        self.cam12_raw.stop()
    def cam12_analytics_stop(self): 
        self.cam12_analytics.stop()



import rec
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Live_view()
    app.exec_()
