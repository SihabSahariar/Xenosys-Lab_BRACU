## Code Xenosys Lab
## Developed by Sami Sadat
from cv import model

def center_obj(lis):
    if len(lis) == 0:
        x=0
        y=0
        
    elif len(lis) != 0:
        x=((lis[0][2]+lis[0][0])//2)
        y=((lis[0][3]+lis[0][1])//2)
    
    lis2=[x,y]
    return lis2 

# torch.div(a, b, rounding_mode='trunc')
def fire_detect():
    import cv2 as cv2
    import numpy as np
    import time
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        fire = False
        frame=cv2.flip(frame,1)
        results = model(frame)

        
        cv2.imshow('YOLO', np.squeeze(results.render()))
        # print("----")
        co_ordinates = (center_obj(results.xyxy[0]))
        if co_ordinates[0]!=0 and co_ordinates[1]!=0:
            fire = True
        
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    return fire
    cap.release()
    cv2.destroyAllWindows()

fire_detect()
