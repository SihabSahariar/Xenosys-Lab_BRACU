from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QSizePolicy, QDialog, QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QApplication)
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot, Qt, QSize, QTimer, QTime, QDate, QObject, QEvent)
from PyQt5.QtGui import (QImage, QPixmap, QFont, QIcon, QColor)

from functools import partial
from threading import Lock
import numpy as np
import time
import cv2
import os
import pickle
import cvzone
import time
import requests
import numpy as np
import onnxruntime as ort
from PIL import Image
from pathlib import Path
from collections import OrderedDict,namedtuple
import random

## Code Xenosys Lab
## Developed by Sami Sadat
from cv import model


	
class detectFire(QThread):
	imgSignal = pyqtSignal(np.ndarray, int, bool)
	def __init__(self, parent, cam_link, index):
		QThread.__init__(self, parent)
		self._lock = Lock()
		self.frame_miss = 6
		self.threshold = 0.45
		self.p = parent
		self.cam_link = cam_link
		self.index = index
		self.threadactive = True

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
				self.img =cv2.cvtColor(self.img,cv2.COLOR_BGR2RGB)				
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
			image = self.img.copy()

			# Write Code For Processing
			frame = image
			frame=cv2.flip(frame,1)
			results = model(frame)
			image = np.squeeze(results.render())

			if self.cam_link==0:
				scale_percent = 100 
			else:
				scale_percent = 40
			width = int(self.img.shape[1] * scale_percent / 100)
			height = int(self.img.shape[0] * scale_percent / 100)
			dim = (width, height)
			self.img = cv2.resize(self.img, dim, interpolation = cv2.INTER_AREA)
			#self.img = cv2.cvtColor(self.img,cv2.COLOR_BGR2RGB)

			self.imgSignal.emit(image, self.index, True)
			
			#cv2.waitKey(capture_delay) & 0xFF # works, dont set 1, will crash, too fast
		
		self.img = np.zeros((400,400,3), np.uint8)
		self.imgSignal.emit(self.img, self.index, False)
		#cv2.waitKey(capture_delay) & 0xFF # works, dont set 1, will crash, too fast
		self.cap.release()


	def stop(self):
		self.threadactive = False
		self.wait()
		#self._lock.release()
		self.cap.release()
		cv2.destroyAllWindows()

	def overlap(self,R1):
		for i, R2 in enumerate(self.posList):
			if (R1[0]>=R2[2]) or (R1[2]<=R2[0]) or (R1[3]<=R2[1]) or(R1[1]>=R2[3]):
				pass
			else:
				return i + 1
		return -1

	def checkpos(self,cord):
		x, y = cord[0], cord[1]
		for i, pos in enumerate(self.posList):
			x1, x2 = min(pos[0], pos[2]), max(pos[0], pos[2])
			y1, y2 = min(pos[1], pos[3]), max(pos[1], pos[3])

			if (x > x1 and x < x2 and y > y1 and y < y2) :
				return i + 1

		return -1

	def letterbox(self,im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleup=True, stride=32):
		# Resize and pad image while meeting stride-multiple constraints
		shape = im.shape[:2]  # current shape [height, width]
		if isinstance(new_shape, int):
			new_shape = (new_shape, new_shape)

		# Scale ratio (new / old)
		r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
		if not scaleup:  # only scale down, do not scale up (for better val mAP)
			r = min(r, 1.0)

		# Compute padding
		new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
		dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

		if auto:  # minimum rectangle
			dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding

		dw /= 2  # divide padding into 2 sides
		dh /= 2

		if shape[::-1] != new_unpad:  # resize
			im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
		top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
		left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
		im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
		return im, r, (dw, dh)

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

