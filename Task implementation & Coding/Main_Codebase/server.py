import sys
from PyQt5 import QtWidgets, QtCore
from paho.mqtt import client as mqtt

class ReceiveText(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xenosys Lab Feedback Tester")
        self.mqttc = mqtt.Client()
        self.mqttc.on_message = self.on_message
        self.mqttc.connect("test.mosquitto.org", 1883)
        self.mqttc.subscribe("test")
        self.mqttc.loop_start()

        self.text_output = QtWidgets.QLabel(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.text_output)

    def on_message(self, client, userdata, msg):
        self.text_output.setText(msg.payload.decode())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    receive_text = ReceiveText()
    receive_text.show()
    sys.exit(app.exec_())
