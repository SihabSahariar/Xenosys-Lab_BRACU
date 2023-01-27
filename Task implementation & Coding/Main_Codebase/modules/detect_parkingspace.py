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

cuda = False
w = 'yolov7-tiny_c27.onnx'
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
session = ort.InferenceSession(w, providers=providers)
	
capture_delay = 100 # 100ms , Dont set 1, too fast, crash
class detectparking(QThread):
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
		self.names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 
				'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 
				'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
				'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 
				'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
				'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 
				'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 
				'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 
				'hair drier', 'toothbrush']
		self.colors = {name:[random.randint(0, 255) for _ in range(3)] for i,name in enumerate(self.names)}		
		try:
			with open(r'modules/parking/thresh.txt','r+') as f:
				x = f.read()
				ls = x.split(',')
				self.threshold = []
				for i in ls:
					self.threshold.append(float(i))
				print(self.threshold)
		except:
			pass
		try:
			with open(r'modules/parking/skip.txt','r+') as f:
				self.skip = f.read()
				self.frame_miss = int(self.skip)
		except:	
			pass



		try:
			with open(f'modules/parking/{index}', 'rb') as f:
			    self.posList = pickle.load(f)
		except:
			print('pickle load error')

	def run(self):
		with self._lock:
			c = 0
			# used to record the time when we processed last frame
			prev_frame_time = 0
			
			# used to record the time at which we processed current frame
			new_frame_time = 0
						
			self.cap = cv2.VideoCapture(self.cam_link)
			self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # set buffer size 
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
			print(self.threshold[self.index],self.frame_miss)	
		while self.cap.isOpened() and self.threadactive:
			# Handle Frame Reading Problems
			try:
				has, self.img = self.cap.read()
				self.img = cv2.cvtColor(self.img,cv2.COLOR_BGR2RGB)				
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
			c = c + 1
			if(c % self.frame_miss != 0):
				continue

			image = self.img.copy()
			image, ratio, dwdh = self.letterbox(image, auto=False)
			image = image.transpose((2, 0, 1))
			image = np.expand_dims(image, 0)
			image = np.ascontiguousarray(image)

			im = image.astype(np.float32)
			im /= 255
			# im.shape

			outname = [i.name for i in session.get_outputs()]
			#outname

			inname = [i.name for i in session.get_inputs()]
			#inname

			inp = {inname[0]:im}

			# ONNX inference
			outputs = session.run(outname, inp)[0]

			ori_images = [self.img.copy()]
			total_parking = 0
			
			for i,(batch_id,x0,y0,x1,y1,cls_id,score) in enumerate(outputs):
			# for batch_id,x0,y0,x1,y1,cls_id,score in outputs:
				# print(batch_id)
				image = ori_images[int(batch_id)]
				box = np.array([x0,y0,x1,y1])
				# print((int(x0),int(y0),int(x1),int(y1)))
				box -= np.array(dwdh*2)
				box /= ratio
				box = box.round().astype(np.int32).tolist()
				cls_id = int(cls_id)
				score = round(float(score),3)
				name = self.names[cls_id]
				color = self.colors[name]
				name += ' '+str(score)
				thickness=-1
				radius=5
				# color=(0, 0, 255)
				###############################################################

				#################################################################
				if(score > self.threshold[self.index]):
					xx0, yy0, xx1, yy1 = box
					center_coordinates = ((xx0+xx1)/2, (yy0+yy1)/2)
					# print(box[:2],box[2:])
					cord = (int(center_coordinates[0]), int(center_coordinates[1]))
					# position = checkpos(cord)
					position = self.overlap(box)

					if(position != -1):
						cv2.rectangle(image,tuple(box[:2]),tuple(box[2:]),color,2)
						total_parking = total_parking + 1
						name = "pos-" + str(position)
						#print(name)
						cv2.circle(image,(int(center_coordinates[0]), int(center_coordinates[1])),5,(0,0,255),cv2.FILLED)
						cv2.putText(image,name,(box[0], box[1] - 2),cv2.FONT_HERSHEY_SIMPLEX,0.75,[225, 255, 255],thickness=2)  
				##################################################################
			cvzone.putTextRect(image, f'Free Space: {total_parking}/{len(self.posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0,200,0))

			new_frame_time = time.time()
			fps = self.frame_miss/(new_frame_time-prev_frame_time)
			# print(fps)
			prev_frame_time = new_frame_time
			#image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)		
			#Resize Image For Lower Memory Consumtion
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
