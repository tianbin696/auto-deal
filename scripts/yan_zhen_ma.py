#!/bin/env python
# -*- coding: utf-8 -*-
import pytesseract
from PIL import Image

def get_vcode(image_path):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    image = Image.open(image_path)
    box = image.copy() #直接复制图像
    box = (186, 90, 254, 110)
    region = image.crop(box)
    vcode = pytesseract.image_to_string(region)
    return vcode

if __name__ == "__main__":
    vcode = get_vcode("verify_code.png")
    print("vode: %s" % vcode)