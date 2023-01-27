# Developed By Xenosys Lab
'''
Module : config
Responsibilities : AI analytics configurations  
'''
class settings():
	def __init__(self):
		try:
			with open(r'modules/parking/thresh.txt','r+') as f:
				self.thr = f.read()
				# ls = x.split(',')
				# self.thr = []
				# for i in ls:
				# 	self.thr.append(float(i))
		except:
			pass
		try:
			with open(r'modules/parking/skip.txt','r+') as f:
				self.skip = f.read()
				# ls = x.split(',')
				# self.thr = []
				# for i in ls:
				# 	self.thr.append(float(i))
		except:
			pass

	def getThresh(self):
		return self.thr
	def getSkip(self):
		return self.skip
	def saveThresh(self,txt):
		#print(txt)
		try:
			with open(r'modules/parking/thresh.txt','r+') as f:
				f.write(txt)

		except:
			pass		
	def saveSkip(self,txt):
		#print(txt)
		try:
			with open(r'modules/parking/skip.txt','r+') as f:
				f.write(txt)
		except:
			pass