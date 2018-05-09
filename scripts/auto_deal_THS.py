#/bin/env python

import datetime
import threading
import time
import pickle

import tkinter.messagebox

import pywinauto
import pywinauto.clipboard
import pywinauto.application
from pywinauto import remote_memory_block
from pywinauto import keyboard
from pywinauto import timings

import tushare as ts

stock_codes = []

class OperationOfThs:
    def __init__(self):
        print("Init THS operations ...")
        self.__app = pywinauto.application.Application()
        try:
            self.__app.connect(title = '网上股票交易系统5.0')
            top_window = pywinauto.findwindows.find_window(title='网上股票交易系统5.0')
            dialog_window = pywinauto.findwindows.find_windows(top_level_only=False, class_name='#32770', parent=top_window)[0]
            wanted_window = pywinauto.findwindows.find_windows(top_level_only=False, parent=dialog_window)

            if len(wanted_window) == 0:
                tkinter.messagebox.showerror('错误', '无法获得“同花顺双向委托界面”的窗口句柄,请将同花顺交易系统切换到“双向委托界面”！')
                exit()

            self.__main_window = self.__app.window_(handle=top_window)
            self.__dialog_window = self.__app.window_(handle=dialog_window)
        except:
            print("Error during init THS")

    def __buy(self, code, price, quantity):
        print("Trying to buy: [%s - %d - %d]" % (code, price, quantity))
        keyboard.SendKeys("{F1}")
        self.__dialog_window.print_control_identifiers()

        self.__dialog_window.Edit1.SetFocus()
        time.sleep(0.5)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(0.5)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(0.5)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(0.5)

        if quantity > 0:
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(0.5)
        self.__dialog_window.Button1.Click()
        time.sleep(0.5)

    def __sell(self, code, price, quantity):
        print("Trying to sell: [%s - %d]" % (code, quantity))
        keyboard.SendKeys("{F2}")
        self.__dialog_window.print_control_identifiers()

        self.__dialog_window.Edit1.SetFocus()
        time.sleep(0.5)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(0.5)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(0.5)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(0.5)

        if quantity > 0:
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(0.5)
        self.__dialog_window.Button2.Click()
        time.sleep(0.5)

    def __closePopupWindows(self):
        print("Closing popup windows")
        while self.__closePopupWindow():
            time.sleep(0.5)

    def __closePopupWindow(self):
        print("Closing popup window")
        popup_window = self.__main_window.PopupWindow()
        if popup_window:
            popup_window = self.__app.window_(handle=popup_window)
            popup_window.SetFocus()
            popup_window.Button.Click()
            return True
        return False

    def order(self, code, direction, price, quantity):
        print("Trying to order: [%s - %s - %d - %d]" % (code, direction, price, quantity))
        self.maxWindow()
        if direction == 'B':
            self.__buy(code, price, quantity)
        if direction == 'S':
            self.__sell(code, price, quantity)
        self.__closePopupWindows()
        self.minWindow()

    def maxWindow(self):
        print("Max current window")
        if self.__main_window.GetShowState() != 3:
            self.__main_window.Maximize()
        self.__main_window.SetFocus()

    def minWindow(self):
        print("Min current window")
        if self.__main_window.GetShowState() != 2:
            self.__main_window.Minimize()


class Monitor:
    def __init__(self):
        print("Trying to Init monitor ...")
        self.loopMonitor()

    def loopMonitor(self):
        print("Start loop monitor ...")
        operation = OperationOfThs()
        code = "600570"
        self.getRealTimeData(code)
        self.getHistoryDayKAvgData(code, "2018-05-01", "2018-05-09")
        operation.order(code, "S", 14, 100)

    def getRealTimeData(self, code):
        print("Trying to get real time stock data: [%s]" % code)
        df = ts.get_realtime_quotes(code)
        print("Realtime data of %s: " %(code))
        print(df)

    def getHistoryDayKAvgData(self, code, startDay, endDay):
        print("Trying to get historical data for: %s - [%s - %s]" % (code, startDay, endDay))
        df = ts.get_hist_data(code, start=startDay, end=endDay)
        print("Historical avg data of %s" % (code))
        print(df)

class MainGui:
    def __init__(self):
        print("Trying to init MainGui ...")

if __name__ == '__main__':
    t1 = threading.Thread(target=MainGui)
    t1.start()
    t2 = threading.Thread(target=Monitor)
    t2.start()
