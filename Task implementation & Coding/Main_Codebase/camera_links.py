# Developed By Xenosys Lab
'''
Module : camera_links
Responsibilities : Camera Data Fetch From Database  
'''
from db import DataBase
db = DataBase("modules/databases/device_info.db")
class cameraConnect:
	def __init__(self):
		self.cameralist = []
		self.AddInfo = []
	def LoadCam(self):
		rawData = db.fetch()
		Data = list(rawData) 
		listData = []
		for i in Data:
			raw = list(i)
			#print(raw)
			if(raw[4]=="IP"):
				user,password,ip = raw[7],raw[8],raw[5]
				#print(user,password,ip)
				#rtsp = f"rtsp://{user}:{password}@{ip}/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
				rtsp = ip 
				self.cameralist.append(rtsp)
			else:
				self.cameralist.append(raw[5])
		return self.cameralist

	def LoadInfo(self):
		rawData = db.fetch()
		Data = list(rawData) 
		listData = []
		for i in Data:
			raw = list(i)
			add_info = raw[2]
			self.AddInfo.append(add_info)
		return self.AddInfo


