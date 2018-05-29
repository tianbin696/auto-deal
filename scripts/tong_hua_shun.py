#!/bin/env python

import pytz
import pywinauto
import pywinauto.application
import pywinauto.clipboard
from pywinauto import keyboard
from pywinauto import mouse
from pywinauto import win32defines
from pywinauto.win32functions import SetForegroundWindow, ShowWindow
import time


def start():
    mouse.double_click(coords=(40, 40))
    time.sleep(10)
    # main_window = pywinauto.application.Application().connect(title = u"委托下单").top_window()
    # main_window.print_control_identifiers()

def restore():
    main_window = pywinauto.application.Application().connect(title =  u'网上股票交易系统5.0').top_window()
    if main_window.HasStyle(win32defines.WS_MINIMIZE): # if minimized
        ShowWindow(main_window.wrapper_object(), 9) # restore window state
    else:
        SetForegroundWindow(main_window.wrapper_object()) # bring to front

def close():
    restore()
    time.sleep(2)
    keyboard.SendKeys('%{F4}')

if __name__ == "__main__":
    start()
    time.sleep(5)
    close()
	
