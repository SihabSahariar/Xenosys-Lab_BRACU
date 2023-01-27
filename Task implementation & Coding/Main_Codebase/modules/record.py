import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt5 import QtWidgets, QtCore, QtGui
import time
import os
from datetime import datetime
class recordStream(QThread):
    
    def __init__(self, cam_link,index):
        super().__init__()
        self.active = True
        self.folder = f"CAM_{index}"
        self.cam_link = cam_link
        self.path = os.path.expanduser(f'~\\Documents\\{self.folder}')
        print(self.path)
        self.date_now = datetime.now().strftime('%Y%m%d')
        self.output_dir = os.path.join(self.path, 'rtsp_saved', self.date_now)
        os.makedirs(self.output_dir, exist_ok=True)
        self.date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_fpath = os.path.join(self.output_dir, 'saved_{}.mp4'.format(self.date_time))
        print(self.output_fpath)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID') 
        self.out1 = cv2.VideoWriter(self.output_fpath, self.fourcc, 30, (640,480))
    def run(self):
        print("HI")
        self.cap1 = cv2.VideoCapture(0)
        if self.active:            
            self.cap1.set(3, 480)
            self.cap1.set(4, 640)
            self.cap1.set(5, 30)
            while self.active:                      
                ret1, image1 = self.cap1.read()
                if ret1:
                    self.out1.write(image1)     
                self.msleep(10)                      

    def stop(self):
        self.out1.release()



