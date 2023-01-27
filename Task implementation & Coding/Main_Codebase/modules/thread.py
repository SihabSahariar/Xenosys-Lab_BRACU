from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from functools import partial
from threading import Lock
import numpy as np
import time
import cv2
import os
from datetime import datetime
import time
capture_delay = 100 # 100ms , Dont set 1, too fast, crash
from db import DataBase
from camera_links import *
db = DataBase("modules/databases/device_info.db")
vacant = []
class ThreadVideo(QThread):
	imgSignal = pyqtSignal(np.ndarray, int, bool)

	def __init__(self, parent, cam_link, index):
		QThread.__init__(self, parent)
		self._lock = Lock()
		self.p = parent
		self.threadactive = True
		self.cam_link = cam_link
		self.index = index
		self.add_info   = []+(cameraConnect().LoadInfo())
		self.last_option = False
		self._record = None
		self.recordList = []
		for i in range(64):
			self.recordList.append(False)
		try:
			self.additional_info = self.add_info[index]
		except:
			self.additional_info = ""
		# FPS = 1/X
		# X = desired FPS
		
	def run(self):
		with self._lock:
			self.cap = cv2.VideoCapture(self.cam_link)
			self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # set buffer size 
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)		
			while self.cap.isOpened() and self.threadactive:
				# Handle Frame Reading Problems
				try:
					has, self.img = self.cap.read()
					if self.cap.get(1)>self.cap.get(7)-2: #video loop
					    self.cap.set(1,0)
				except:
					#self.record = False
					self.threadactive = False
					cv2.destroyAllWindows()
					self.cap.release()
				if not has:
					self.threadactive = False
					self.cap.release()
					break 
				#Resize Image For Lower Memory Consumtion
				if self.cam_link==0:
					scale_percent = 100 
				else:
					scale_percent = 80
				width = int(self.img.shape[1] * scale_percent / 100)
				height = int(self.img.shape[0] * scale_percent / 100)
				dim = (width, height)
				self.img = cv2.resize(self.img, dim, interpolation = cv2.INTER_AREA)
				self.img = cv2.cvtColor(self.img,cv2.COLOR_BGR2RGB)	
				if self.additional_info != "":
					putBText(self.img,f'Info : {self.additional_info}',text_offset_x=10,text_offset_y=60,vspace=20,hspace=10, font_scale=0.8,background_RGB=(100,20,222),text_RGB=(255,255,255))		
				putBText(self.img,f'Camera {self.index+1}',text_offset_x=10,text_offset_y=10,vspace=10,hspace=10, font_scale=0.8,background_RGB=(10,20,222),text_RGB=(255,255,255))																
				self.imgSignal.emit(self.img, self.index, True)
				
				#print(self.index)
				if(self._record==True and self.recordList[self.index]==False):
					# Run Recorder thread
					self.recordList[self.index]= True
					print("RUN VIDEO RECORDER FOR",self.cam_link)
				elif(self._record==False and self.recordList[self.index]==True):
					# Run stop thread
					self.recordList[self.index]= False
					print("Stop Recorder For",self.cam_link)
					
		cv2.destroyAllWindows()
		self.cap.release()
		self.quit()
	def stop(self):
		try:
			self.threadactive = False
			cv2.destroyAllWindows()
			self.cap.release()
			self.quit()
			#self._lock.release()	
		except:
			pass
    #    # Use a property to control access to a via our lock
	# @property
	# def record(self):
	# 	with self._lock:
	# 		return self._record

	# @record.setter
	# def record(self, rec):
	# 	with self._lock:
	# 		self._record = rec
				
#---------------------------Transparent Text-------------------	---------------------------	
def putBText(img,text,text_offset_x=20,text_offset_y=20,vspace=10,hspace=10, font_scale=1.0,background_RGB=(228,225,222),text_RGB=(1,1,1),font = cv2.FONT_HERSHEY_DUPLEX,thickness = 2,alpha=0.6,gamma=0):
	R,G,B = background_RGB[0],background_RGB[1],background_RGB[2]
	text_R,text_G,text_B = text_RGB[0],text_RGB[1],text_RGB[2]
	(text_width, text_height) = cv2.getTextSize(text, font, fontScale=font_scale, thickness=thickness)[0]
	x, y, w, h = text_offset_x, text_offset_y, text_width , text_height
	crop = img[y-vspace:y+h+vspace, x-hspace:x+w+hspace]
	white_rect = np.ones(crop.shape, dtype=np.uint8)
	b,g,r = cv2.split(white_rect)
	rect_changed = cv2.merge((B*b,G*g,R*r))
	res = cv2.addWeighted(crop, alpha, rect_changed, 1-alpha, gamma)
	img[y-vspace:y+vspace+h, x-hspace:x+w+hspace] = res
	cv2.putText(img, text, (x, (y+h)), font, fontScale=font_scale, color=(text_B,text_G,text_R ), thickness=thickness)
	return img
