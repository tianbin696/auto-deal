#/bin/env python

import datetime
import threading
import time
import pickle
import math

import tkinter.messagebox

import pywinauto
import pywinauto.clipboard
import pywinauto.application
from pywinauto import remote_memory_block
from pywinauto import keyboard
from pywinauto import timings

import tushare as ts

stock_codes = ['002024', '002647', '600570']
stock_positions = {'002024':3000, '002647':300, '600570':600}
maxMoney = 10000

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
        keyboard.SendKeys("{F1}")
        time.sleep(1.0)

        # self.__dialog_window.print_control_identifiers()

        self.__dialog_window.Edit1.SetFocus()
        time.sleep(1.0)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(1.0)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(1.0)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(1.0)

        if quantity > 0:
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(1.0)
        self.__dialog_window.Button6.Click()
        time.sleep(1.0)

    def __sell(self, code, price, quantity):
        keyboard.SendKeys("{F2}")
        time.sleep(1.0)

        # self.__dialog_window.print_control_identifiers()

        self.__dialog_window.Edit1.SetFocus()
        time.sleep(1.0)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(1.0)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(1.0)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(1.0)

        if quantity > 0:
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(1.0)
        self.__dialog_window.Button6.Click()
        time.sleep(1.0)

    def __closePopupWindows(self):
        # print("Closing popup windows")
        while self.__closePopupWindow():
            time.sleep(1.0)

    def __closePopupWindow(self):
        # print("Closing popup window")
        popup_window = self.__main_window.PopupWindow()
        if popup_window:
            popup_window = self.__app.window_(handle=popup_window)
            popup_window.SetFocus()
            popup_window.Button.Click()
            return True
        return False

    def order(self, code, direction, price, quantity):
        print("Trying to order: [%s - %s - %d - %d]" % (code, direction, price, quantity))
        try:
            self.maxWindow()
            price = "%.2f" % price
            if direction == 'B':
                self.__buy(code, price, quantity)
            if direction == 'S':
                self.__sell(code, price, quantity)
            self.__closePopupWindows()
            self.minWindow()
        except:
            pass

    def maxWindow(self):
        # print("Max current window")
        if self.__main_window.GetShowState() != 3:
            self.__main_window.Maximize()
        self.__main_window.SetFocus()

    def minWindow(self):
        # print("Min current window")
        if self.__main_window.GetShowState() != 2:
            self.__main_window.Minimize()


class Monitor:

    def __init__(self):
        print("Trying to Init monitor ...")
        self.avg10 = {}
        self.operation = OperationOfThs()

        self.loopMonitor()

    def loopMonitor(self):
        print("Start loop monitor ...")

        for code in stock_codes:
            avg = self.getHistoryDayKAvgData(code)
            self.avg10[code] = avg
        print("Avgs: %s" % self.avg10)

        while True:
            for code in stock_codes:
                price = self.getRealTimeData(code)
                self.makeDecision(code, price)
            break

    def makeDecision(self, code, price):
        direction = self.getDirection(code, price)
        print("Direction for %s: %s" % (code, direction))
        if direction == 'B':
            if code not in stock_positions or stock_positions[code] <= 0:
                buyPrice = self.getBuyPrice(price)
                buyAmount = self.getBuyAmount(price)
                self.operation.order(code, direction, buyPrice, buyAmount)
                stock_positions[code] = buyAmount
        elif direction == 'S':
            if code in stock_positions and stock_positions[code] > 0:
                sellPrice = self.getSellPrice(price)
                sellAmount = self.getSellAmount(code)
                self.operation.order(code, direction, sellPrice, sellAmount)
                stock_positions[code] -= sellAmount
        else:
            print("No action for %s" % code)

    def getRealTimeData(self, code):
        df = ts.get_realtime_quotes(code)
        price = df['price'][0]
        print("Realtime data of %s: %s" %(code, price))
        return float(price)

    def getHistoryDayKAvgData(self, code):
        df = ts.get_hist_data(code)
        total = 0.0
        i = 0
        while i < 10:
            total += df['close'][i]
            i += 1
        avg = total/10
        print("Historical avg data of %s: %f" % (code, avg))
        return float(avg)

    def getDirection(self, code, price):
        avg = float(self.avg10[code])
        price = float(price)

        if price < avg and price > avg * 0.98:
            return 'S'

        if price > avg and price < avg * 1.02:
            return 'B'

        return 'S'

    def getBuyPrice(self, price):
        return price * 1.02

    def getSellPrice(self, price):
        return price * 0.98

    def getBuyAmount(self, price):
        return math.floor(maxMoney/price/100) * 100

    def getSellAmount(self, code):
        return math.ceil(stock_positions[code]/2/100) * 100

class MainGui:
    def __init__(self):
        print("Trying to init MainGui ...")

if __name__ == '__main__':
    t1 = threading.Thread(target=MainGui)
    t1.start()
    t2 = threading.Thread(target=Monitor)
    t2.start()
