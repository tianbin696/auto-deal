#/bin/env python

import datetime
import threading
import time
import pickle
import math
import logging

import tkinter.messagebox

import pywinauto
import pywinauto.clipboard
import pywinauto.application
from pywinauto import remote_memory_block
from pywinauto import keyboard
from pywinauto import timings

import tushare as ts

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../auto_deal_ths.log',
                    filemode='a')
#################################################################################################
#定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
#################################################################################################

stock_codes = ['002024', '002647', '600570', '600585','600690','001979','600048','600201','000333','002120','600801','002372','600566']
stock_positions = {}
stock_ordered = []

maxMoney = 10000
sleepTime = 1.0
monitorInterval = 30

class OperationOfThs:
    def __init__(self):
        logging.info("Init THS operations ...")
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
            logging.info("Error during init THS")

    def __buy(self, code, price, quantity):
        keyboard.SendKeys("{F1}")
        time.sleep(sleepTime)

        # self.__dialog_window.logging.info_control_identifiers()

        self.__dialog_window.Edit1.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(sleepTime)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(sleepTime)

        if quantity > 0:
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(sleepTime)
        self.__dialog_window.Button6.Click()
        time.sleep(sleepTime)

    def __sell(self, code, price, quantity):
        keyboard.SendKeys("{F2}")
        time.sleep(sleepTime)

        # self.__dialog_window.logging.info_control_identifiers()

        self.__dialog_window.Edit1.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(sleepTime)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(sleepTime)

        if quantity > 0:
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(sleepTime)
        self.__dialog_window.Button6.Click()
        time.sleep(sleepTime)

    def __closePopupWindows(self):
        # logging.info("Closing popup windows")
        while self.__closePopupWindow():
            time.sleep(sleepTime)

    def __closePopupWindow(self):
        # logging.info("Closing popup window")
        popup_window = self.__main_window.PopupWindow()
        if popup_window:
            popup_window = self.__app.window_(handle=popup_window)
            popup_window.SetFocus()
            popup_window.Button.Click()
            return True
        return False

    def refresh(self, t=0.5):
        """
        点击刷新按钮
        :param t:刷新后的等待时间
        """
        self.__dialog_window.Button4.Click()
        time.sleep(t)

    def getPosition(self):
        position = self.__getCleanedData()
        for index in range(1, len(position)):
            code = position[index][1]
            amount = position[index][4]
            stock_positions[code] = int(amount)

        logging.info("Positions: %s" % stock_positions)

    def __getCleanedData(self, cols = 16):
        self.maxWindow()
        time.sleep(sleepTime)

        keyboard.SendKeys("{F4}")
        time.sleep(sleepTime)

        # self.__dialog_window.print_control_identifiers()
        # self.refresh(sleepTime)

        self.__dialog_window.CVirtualGridCtrl.RightClick(coords=(30, 30))
        time.sleep(sleepTime)
        self.__main_window.TypeKeys('C')
        time.sleep(sleepTime)

        data = pywinauto.clipboard.GetData()
        lst = data.strip().split("\r\n")
        matrix = []
        for i in range(0, len(lst)):
            subList = lst[i].split("\t")
            matrix.append(subList)

        self.minWindow()
        return matrix

    def order(self, code, direction, price, quantity):
        logging.info("Trying to order: [%s - %s - %d - %d]" % (code, direction, price, quantity))
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
        # logging.info("Max current window")
        if self.__main_window.GetShowState() != 3:
            self.__main_window.Maximize()
        self.__main_window.SetFocus()

    def minWindow(self):
        # logging.info("Min current window")
        if self.__main_window.GetShowState() != 2:
            self.__main_window.Minimize()


class Monitor:

    def __init__(self):
        logging.info("Trying to Init monitor ...")
        self.avg1 = {}
        self.avg10 = {}
        self.avg20 = {}
        self.operation = OperationOfThs()

        self.loopMonitor()

    def loopMonitor(self):
        logging.info("Start loop monitor ...")

        for code in stock_codes:
            avg = self.getHistoryDayKAvgData(code, 1)
            self.avg1[code] = avg

            avg = self.getHistoryDayKAvgData(code, 10)
            self.avg10[code] = avg

            avg = self.getHistoryDayKAvgData(code, 20)
            self.avg20[code] = avg
        logging.info("Avgs 1: %s" % self.avg1)
        logging.info("Avgs 10: %s" % self.avg10)
        logging.info("Avgs 20: %s" % self.avg20)

        self.operation.getPosition() #开盘前获取持仓情况

        while True:
            now = time.localtime(time.time())
            if now.tm_hour > 15:
                logging.info("Closing deal") #闭市
                break
            print()
            logging.info("looping monitor stocks")
            for code in stock_codes:
                price = self.getRealTimeData(code)
                self.makeDecision(code, price)

            time.sleep(monitorInterval)

    def makeDecision(self, code, price):
        direction = self.getDirection(code, price)
        logging.info("Direction for %s: %s" % (code, direction))
        if code not in stock_ordered:
            if direction == 'B':
                if code not in stock_positions or stock_positions[code] <= 0:
                    buyPrice = self.getBuyPrice(price)
                    buyAmount = self.getBuyAmount(price)
                    self.operation.order(code, direction, buyPrice, buyAmount)
                    stock_positions[code] = buyAmount
                    stock_ordered.append(code)
            elif direction == 'HS' or direction == 'FS':
                if code in stock_positions and stock_positions[code] > 0:
                    sellPrice = self.getSellPrice(price)
                    sellAmount = self.getSellAmount(code)
                    if direction == 'FS':
                        sellAmount = stock_positions[code]
                    self.operation.order(code, direction, sellPrice, sellAmount)
                    stock_positions[code] -= sellAmount
                    stock_ordered.append(code)
            else:
                logging.info("No action for %s" % code)
        else:
            logging.info("Already ordered today, ignore %s" % code)

    def getRealTimeData(self, code):
        df = ts.get_realtime_quotes(code)
        price = df['price'][0]
        logging.info("Realtime data of %s: %s" %(code, price))
        return float(price)

    def getHistoryDayKAvgData(self, code, days):
        df = ts.get_hist_data(code)
        total = 0.0
        i = 0
        while i < days:
            total += df['close'][i]
            i += 1
        avg = total/days
        logging.info("Historical %d avg data of %s: %f" % (days, code, avg))
        return float(avg)

    def getDirection(self, code, price):
        avg1 = float(self.avg1[code])
        avg10 = float(self.avg10[code])
        avg20 = float(self.avg20[code])
        price = float(price)

        if price < avg1 and price < avg10 and price > avg10 * 0.98: #股价跌破10日均值，卖半仓
            return 'HS'

        if price < avg1 and price < avg20 and price > avg20 * 0.98: #股价跌破20日均值，卖全仓
            return 'FS'

        if price > avg1 and avg10 > avg20 and price > avg10 and price < avg10 * 1.02: #股价突破10日均值，且大于20日均值
            return 'B'

        return 'N'

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
        logging.info("Trying to init MainGui ...")

if __name__ == '__main__':
    # operation = OperationOfThs()
    # operation.getPosition()

    t1 = threading.Thread(target=MainGui)
    t1.start()
    t2 = threading.Thread(target=Monitor)
    t2.start()
