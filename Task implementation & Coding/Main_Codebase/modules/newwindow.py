from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, QSizePolicy, QDialog, QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QApplication)
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot, Qt, QSize, QTimer, QTime, QDate, QObject, QEvent)
from PyQt5.QtGui import (QImage, QPixmap, QFont, QIcon, QColor)

from functools import partial
from threading import Lock
import numpy as np
import time
import cv2
import os
# width, height = 480*4, 640*4
width, height = 480*6, 270*6
# capture_delay = 10000 # 10 seconds
capture_delay = 100 # 100ms , Dont set 1, too fast, crash

class NewWindow(QDialog):
	def __init__(self, parent):
		QDialog.__init__(self, parent)
		self.p = parent
		self.index = None

		self.lbl_cam = QLabel()
		self.lbl_cam.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
		self.lbl_cam.setScaledContents(True)
		self.lbl_cam.setFont(QFont("Times", 15))
		self.lbl_cam.setStyleSheet(
			"color: rgb(255,255,255);"
			"background-color: rgb(0,0,0);"
			"qproperty-alignment: AlignCenter;")

		layout = QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		# layout.setSpacing(2)
		layout.addWidget(self.lbl_cam)
		self.setLayout(layout)
		self.setWindowTitle('Camera {}'.format(self.index))
		#self.showMaximized()

	def sizeHint(self):
		return QSize(width//4, height//4)

	def resizeEvent(self, event):
		self.update()

	def close(self):
		self.accept()

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Escape:
			self.accept()
