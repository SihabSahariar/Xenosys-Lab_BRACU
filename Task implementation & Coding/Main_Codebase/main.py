# Developed By Xenosys Lab
'''
Module : main
Responsibilities : Load splash screen and manage login credentials
System Login : Username - admin password - admin 
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent, QCursor
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from db import DataBase
from home_ import *
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        loadUi("Forms/login.ui",self)
        QShortcut(QtCore.Qt.Key_Enter, self, self.loginCheck)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.center()
        self.oldPos = self.pos()
        self.pushButton_2.clicked.connect(self.closeWindow)
        self.pushButton.clicked.connect(self.loginCheck)
        self.lineEdit_2.returnPressed.connect(self.loginCheck)
        self.lineEdit.returnPressed.connect(self.loginCheck)
        self.movie = QMovie(":/icon/icon/Media1.gif")
        self.gif.setMovie(self.movie)
        self.movie.start()

    def loginCheck(self):
        if self.lineEdit.text()==query.value(0) and self.lineEdit_2.text()==query.value(1):
            self.ShowHome()
            self.close()
        else:
            if self.lineEdit_2.text()=="":
                self.lineEdit_2.setFocus()  
            if self.lineEdit.text()=="":
                self.lineEdit.setFocus()
              
            return QMessageBox.critical(self, "Failed", "Login Failed")

    def ShowHome(self):
        self.window = Home()
        self.window.show()
        #self.window.showMaximized()
    # Center the screen
    def center(self):
        ref = self.frameGeometry()
        place = QtWidgets.QDesktopWidget().availableGeometry().center()
        ref.moveCenter(place)
        self.move(ref.topLeft())

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    # Minimize window
    def hideWindow(self):
        self.showMinimized()

    # Close window
    def closeWindow(self):
        self.close()


def createConnection():
    global query
    con = QtSql.QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName("modules/databases/login.sqlite")
    if not con.open():
        QMessageBox.critical(
            None,
            "Database Error",
            "Database Error: %s" % con.lastError().databaseText(),
        )
        return False
    query = QtSql.QSqlQuery("select * from userdata")
    query.first()
    return True

from PyQt5 import QtSql
import sys
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #app.setStyleSheet(qdarktheme.load_stylesheet("light")) 
    if not createConnection():
        sys.exit(1)
    main = MainWindow()
    main.show()

    sys.exit(app.exec_())