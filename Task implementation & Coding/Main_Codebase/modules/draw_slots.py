import cv2
import numpy as np
import pickle


class draw:
    def __init__(self,cam_link,pickle_file):
        self.drawing = False # true if mouse is pressed
        self.mode = True # if True, draw rectangle. Press 'm' to toggle to curve
        self.ix,self.iy = -1,-1
        self.x_, self.y_ = 0,0
        self.r = 15 #circle radius
        self.picklefile = pickle_file
        self.camlink = cam_link
        self.posList = []
        self.prevposList = []

        try:
            with open(f'modules/parking/{self.picklefile}', 'rb') as f:
                self.posList = pickle.load(f)
        except:
            self.posList = []
            pickle.dump(self.posList,open(f'modules/parking/{self.picklefile}', "wb"))
        self.vidcap = cv2.VideoCapture(self.camlink)

    # mouse callback function
    def draw_shape(self,event,x,y,flags,param):
        global ix,iy,drawing,mode,x_,y_, r

        if event == cv2.EVENT_LBUTTONDOWN:
            print('inside mouse lbutton event....')
            self.drawing = True
            ix,iy = x,y
            x_,y_ = x,y
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            copy = self.img.copy()
            x_,y_ = x,y
            if self.mode:
                cv2.rectangle(copy,(ix,iy),(x_,y_),(0,255,0),1)
                cv2.imshow("image", copy)
            else:
                cv2.circle(copy,(x,y),r,(0,0,255),1)
                cv2.imshow('image', copy)
        #
        elif event == cv2.EVENT_LBUTTONUP:
            print('inside mouse button up event')
            self.drawing = False
            if self.mode:
                # cv2.rectangle(img,(ix,iy),(x,y),(0,255,0),1)
                self.posList.append((ix,iy, x, y))
            else:
                cv2.circle(self.img,(x,y),r,(0,0,255),1)
        if event == cv2.EVENT_RBUTTONDOWN:
            for i, pos in enumerate(self.posList):
                px, py, qx, qy = pos

                
                if min(px, qx) < x < max(px, qx) and min(py, qy) < y < max(py, qy):
                    print(i)
                    self.posList.pop(i)
        
                with open(f'modules/parking/{self.picklefile}', 'wb') as f:
                    pickle.dump(self.posList, f)

    def slot_akao(self):
        success,self.image = self.vidcap.read()
        count = 0
        while success:     
          success,image = self.vidcap.read()
          count += 1
          break

        self.img = self.image.copy()
        temp_img = np.copy(self.img)
        cv2.namedWindow('image')
        cv2.setMouseCallback('image',self.draw_shape)
        self.prevposList = []
        while(1):
            # print('inside while loop...')
            cv2.imshow('image',self.img)
            if not cv2.EVENT_MOUSEMOVE:
                copy = self.img.copy()
            with open(f'modules/parking/{self.picklefile}', 'wb') as f:
                pickle.dump(self.posList, f)
            for pos in self.posList:
                #print(pos)
                px, py, qx, qy = pos
                cv2.rectangle(copy, (px, py), (qx, qy), (255, 0, 255), 2)
                cv2.imshow('image',copy)
            
            k = cv2.waitKey(1) & 0xFF
            if cv2.getWindowProperty('image', cv2.WND_PROP_VISIBLE) <1:
                break
        cv2.destroyAllWindows()
'''
if __name__ == '__main__':
    x = draw(cam_link='carpark.mp4',pickle_file = '1')
    x.slot_akao()
'''