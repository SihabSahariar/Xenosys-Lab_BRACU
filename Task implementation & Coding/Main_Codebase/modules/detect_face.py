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
import mediapipe as mp

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

capture_delay = 100 # 100ms , Dont set 1, too fast, crash
#face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


 
class detectFace(QThread):
	imgSignal = pyqtSignal(np.ndarray, int, bool)

	def __init__(self, parent, cam_link, index):
		QThread.__init__(self, parent)
		#self._lock = Lock()
		self.p = parent
		self.cam_link = cam_link
		self.index = index
		self.threadactive = True
		self.cap = cv2.VideoCapture(self.cam_link)
	def run(self):
		#with self._lock:

		#cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)

		prevTime = 0
		with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:		
			while self.cap.isOpened() and self.threadactive:
				has, self.img = self.cap.read()
				if not has: break # video has limit
				try:		
					
					self.img.flags.writeable = False
					results = face_detection.process(self.img)
					# Draw the face detection annotations on the self.img.
					self.img.flags.writeable = True
					self.img = cv2.cvtColor(self.img, cv2.COLOR_RGB2BGR)
					if results.detections:
					    for detection in results.detections:
					        mp_drawing.draw_detection(self.img, detection)

					currTime = time.time()
					fps = 1 / (currTime - prevTime)
					prevTime = currTime
					cv2.putText(self.img, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_PLAIN, 3, (0, 196, 255), 2)
					#self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)					
					self.imgSignal.emit(self.img, self.index, True)

				except:
					pass
		
		self.img = np.zeros((400,400,3), np.uint8)
		self.imgSignal.emit(self.img, self.index, False)
		#cv2.waitKey(capture_delay) & 0xFF # works, dont set 1, will crash, too fast
		self.cap.release()
		cv2.destroyAllWindows()
	


	def stop(self):
		self.threadactive = False
		self.wait()
		#self._lock.release()
		self.cap.release()
		cv2.destroyAllWindows()
