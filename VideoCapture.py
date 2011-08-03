#!/usr/bin/python
"""VideoCapture.py

Actually a fake one based on opencv for linux compatibility

"""

import cv
import Image

class Device:
    def __init__(self, camnum = -1):
        self.camera = cv.CreateCameraCapture(camnum)
        self.base = cv.QueryFrame(self.camera)
        self.size = self.width, self.height = cv.GetSize(self.base)
        self.depth = self.base.depth
        self.nChannels = self.base.nChannels

    def getImage(self):
        img = cv.QueryFrame(self.camera)
        cv.CvtColor(img, img, cv.CV_BGR2RGB)
        return Image.fromstring("RGB", cv.GetSize(img), img.tostring())
