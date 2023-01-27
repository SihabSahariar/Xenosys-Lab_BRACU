# Developed By Xenosys Lab
'''
Module : Rec
Responsibilities : RTSP Recording module
Integration : NO
'''
from threading import Thread
import imutils
import cv2, time
import sys
import time
import os
from datetime import datetime

class VideoStreamWidget(object):
    def __init__(self, cam_link,index):
        self.folder = f"CAM_{index}"
        self.cam_link = cam_link
        self.path = os.path.expanduser(f'~\\Documents\\{self.folder}')
        print(self.path)
        self.date_now = datetime.now().strftime('%Y%m%d')
        self.output_dir = os.path.join(self.path, 'rtsp_saved', self.date_now)
        os.makedirs(self.output_dir, exist_ok=True)
        self.date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_fpath = os.path.join(self.output_dir, 'saved_{}.avi'.format(self.date_time))
        print(self.output_fpath)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID') 
        self.out = cv2.VideoWriter(self.output_fpath, self.fourcc, 30, (640,480))
        self.capture = cv2.VideoCapture(self.cam_link)
        self.thread = Thread(target=self.update, args=())
        #self.thread.daemon = True
        self.thread.start()        
    def update(self):
        # Read the next frame from the stream in a different thread
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
                self.out.write(self.frame)

    def stop(self):
        try:
        	self.thread.stop()
        	self.out.release()
	        self.capture.release()
	        cv2.destroyAllWindows()
	        print("Stopped")
	        exit(1)
        except:
	            pass

def run(cam_url,cam_index):
    video_stream_widget = VideoStreamWidget(int(cam_url),cam_index)

import multiprocessing
if __name__ == '__main__':
    n = len(sys.argv)
    lst = []
    for i in range(1, n):
        lst.append(sys.argv[i])  
    print(lst)
    proc = multiprocessing.Process(target=run, args=(lst[0],lst[1]))
    proc.start()
    # x = input()
    # if x=='-' and proc.is_alive():
    # 	proc.terminate()
    # 	sys.exit()