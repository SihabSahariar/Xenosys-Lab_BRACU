## Code Xenosys Lab
## Developed by Sami Sadat

import os

import torch 


model = torch.hub.load('ultralytics/yolov5', 'custom', path=r'fire.pt', force_reload=False)

