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
# -----------------------------------------
class TableStatus(QDialog):
	def __init__(self, parent):
		QDialog.__init__(self, parent)
		self.p = parent
		self.table = QTableWidget()
		self.table.setSelectionMode(QAbstractItemView.SingleSelection)
		# self.table.setSelectionMode(QAbstractItemView.MultiSelection)
		self.table.setRowCount(len(self.p.cam_links))
		self.table.setColumnCount(2)
		self.table.setHorizontalHeaderLabels(('ID', 'Status')) # NOTE: after setColumnsCount()
		self.table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.horizontalHeader().setFont(QFont("Times", 13))
		# self.table.verticalHeader().setStretchLastSection(True)
		# self.table.setSortingEnabled(True)
		style = "::section {""background-color: darkcyan; color: rgb(230,230,230);}"
		self.table.horizontalHeader().setStyleSheet(style)
		self.table.verticalHeader().setStyleSheet(style)
		# self.table.setShowGrid(True)

		self.table.resizeColumnsToContents()
		self.table.resizeRowsToContents()
		# self.table.sortByColumn(0, Qt.AscendingOrder)
		self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read-Only

		# self.table.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

		layout = QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		# layout.setSpacing(2)
		layout.addWidget(self.table)
		self.setLayout(layout)
		self.setWindowTitle('Camera Status')

	def sizeHint(self):
		return QSize(width//4, height//4)

	def resizeEvent(self, event):
		self.update()

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Escape:
			self.accept()
			# self.table.clear()
			self.p.buttonStatus.setStyleSheet(
				"color: rgb(127,255,127); background-color: rgb(0,0,0);")

	def closeEvent(self, event):
		event.accept()
		self.p.buttonStatus.setStyleSheet(
			"color: rgb(127,255,127); background-color: rgb(0,0,0);")

	def updateTable(self, cam_links, actives):
		for i, (cam_link, active) in enumerate(zip(cam_links, actives)):
			# simple
			# self.table.setItem(i,0, QTableWidgetItem(str(cam_link))) # rowi,col0
			# self.table.setItem(i,1, QTableWidgetItem(str(active))) # rowi,col1

			# complex
			col1 = QTableWidgetItem(str(cam_link))
			col1.setFont(QFont("Times", 13))
			col1.setForeground(QColor(127,255,255))				# fg
			if i % 2 == 0: col1.setBackground(QColor(0,0,0))	# bg
			else: col1.setBackground(QColor(61,53,53))			# bg
			col1.setTextAlignment(Qt.AlignLeft)
			self.table.setItem(i,0, col1)

			col2 = QTableWidgetItem(str(active))
			col2.setFont(QFont("Times", 13))
			if active: col2.setForeground(QColor(127,255,127))	# fg
			else: col2.setForeground(QColor(255,127,127))		# fg
			if i % 2 == 0: col2.setBackground(QColor(0,0,0))	# bg
			else: col2.setBackground(QColor(61,53,53))			# bg
			col2.setTextAlignment(Qt.AlignCenter)
			self.table.setItem(i,1, col2)

		self.table.resizeColumnsToContents()
		self.table.resizeRowsToContents()
		# self.resize(QSize(width//4, height//4))

		self.p.buttonStatus.setStyleSheet(
			"color: rgb(255,127,127); background-color: rgb(0,0,0);")


# -----------------------------------------