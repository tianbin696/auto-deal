#/bin/env python

import logging
import math
import threading
import time
import tkinter.messagebox

import pywinauto
import pywinauto.application
import pywinauto.clipboard
import tushare as ts
from pywinauto import keyboard
from timezone_logging.timezone_logging import get_timezone_logger

logger = get_timezone_logger('')

stock_codes = ['002024', '002647', '600570', '600585','600690','001979','600048','600201','000333','002120','600801','002372','600566']
# stock_codes = ['002024', '002647', '600570']
stock_positions = {}
stock_ordered = []
maxMoney = 10000
maxMoneyPerStock = 20000
availableMoney = 20000
sleepTime = 0.5
monitorInterval = 30
sellThreshold = 0.02
buyThreshold = 0.02  # [1-threshold ~ 1+threshold]

class OperationOfThs:
    def __init__(self):
        logger.info("Init THS operations ...")
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
        except Exception as e:
            logger.info("Error during init THS: %s" % e)

    def __buy(self, code, price, quantity):
        keyboard.SendKeys("{F1}")
        time.sleep(sleepTime)
        self.__init__()

        # self.__dialog_window.print_control_identifiers()

        self.__dialog_window.Edit0.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit0.SetEditText(code)
        time.sleep(sleepTime)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(sleepTime)

        self.__dialog_window.Edit3.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit3.SetEditText(quantity)
        time.sleep(sleepTime)

        self.__dialog_window['买入Button'].Click()
        time.sleep(sleepTime)

    def __sell(self, code, price, quantity):
        keyboard.SendKeys("{F2}")
        time.sleep(sleepTime)
        self.__init__()

        # self.__dialog_window.print_control_identifiers()

        self.__dialog_window.Edit0.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit0.SetEditText(code)
        time.sleep(sleepTime)

        self.__dialog_window.Edit2.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit2.SetEditText(price)
        time.sleep(sleepTime)

        self.__dialog_window.Edit3.SetFocus()
        time.sleep(sleepTime)
        self.__dialog_window.Edit3.SetEditText(quantity)
        time.sleep(sleepTime)

        self.__dialog_window.child_window(title="卖出", class_name="Button").Click()
        time.sleep(sleepTime)

    def __closePopupWindows(self):
        # logger.info("Closing popup windows")
        while self.__closePopupWindow():
            time.sleep(sleepTime)

    def __closePopupWindow(self):
        # logger.info("Closing popup window")
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

        logger.info("Positions: %s" % stock_positions)
        if len(stock_positions) <= 0:
            logger.error("Failed to get current position")
            exit(1)

    def __getCleanedData(self, cols = 16):
        # self.maxWindow()
        # time.sleep(sleepTime)

        # keyboard.SendKeys("{F4}")
        # time.sleep(sleepTime)

        # self.__dialog_window.print_control_identifiers()
        # self.refresh(sleepTime)

        # self.__dialog_window.CVirtualGridCtrl.RightClick(coords=(30, 30))
        # time.sleep(sleepTime)
        # self.__main_window.TypeKeys('C')
        # time.sleep(sleepTime)

        data = pywinauto.clipboard.GetData() # Copy from clipboard directly after manual copy
        lst = data.strip().split("\r\n")
        matrix = []
        for i in range(0, len(lst)):
            subList = lst[i].split("\t")
            matrix.append(subList)

        # self.minWindow()
        return matrix

    def order(self, code, direction, price, quantity):
        logger.info("Trying to order: [%s - %s - %d - %d]" % (code, direction, price, quantity))
        try:
            # self.maxWindow()

            price = "%.2f" % price
            if direction == 'B':
                self.__buy(code, price, quantity)
            if direction == 'S':
                self.__sell(code, price, quantity)
            self.__closePopupWindows()
            # self.minWindow()
            return True
        except Exception as e:
            logger.error("Failed to order: %s" % e)
            return False

    def maxWindow(self):
        # logger.info("Max current window")
        if self.__main_window.GetShowState() != 3:
            self.__main_window.Maximize()
        self.__main_window.SetFocus()
        time.sleep(sleepTime)

    def minWindow(self):
        # logger.info("Min current window")
        if self.__main_window.GetShowState() != 2:
            self.__main_window.Minimize()


class Monitor:

    def __init__(self):
        logger.info("Trying to Init monitor ...")
        self.avg1 = {}
        self.avg10 = {}
        self.avg20 = {}
        self.operation = OperationOfThs()
        # self.operation.maxWindow()

        self.loopMonitor()

    def testSellBeforeDeal(self):
        self.operation.order('600570', 'S', 0, 200)

    def testBuyBeforeDeal(self):
        self.operation.order('600570', 'B', 0, 200)

    def loopMonitor(self):
        logger.info("Start loop monitor ...")
        time.sleep(5)
        self.testSellBeforeDeal()
        time.sleep(5)
        self.testBuyBeforeDeal()

        for code in stock_codes:
            avg = self.getHistoryDayKAvgData(code, 1)
            self.avg1[code] = avg

            avg = self.getHistoryDayKAvgData(code, 10)
            self.avg10[code] = avg

            avg = self.getHistoryDayKAvgData(code, 20)
            self.avg20[code] = avg
        logger.info("Avgs 1: %s" % self.avg1)
        logger.info("Avgs 10: %s" % self.avg10)
        logger.info("Avgs 20: %s" % self.avg20)

        self.operation.getPosition() #开盘前获取持仓情况
        isStarted = False

        while True:
            time.sleep(monitorInterval)
            if (self.compare("09", "30") and not self.compare("11", "30")) or (self.compare("13", "00") and not self.compare("15", "00")):
                # 交易时间：[09:30 ~ 11:30, 13:00 ~ 15:00]
                isStarted = True
            else:
                isStarted = False

            if not isStarted:
                logger.info("Not deal window, wait for deal time")
                continue

            print()
            logger.info("looping monitor stocks")
            for code in stock_codes:
                try:
                    price = self.getRealTimeData(code)
                    self.makeDecision(code, price)
                except Exception as e:
                    logger.error("Failed to monitor %s" % code)

    def format(self, num):
        if num < 10:
            return "0%d" % num
        else:
            return "%d" % num


    def compare(self, hour, minute):
        now = time.localtime(time.time())
        targetStr = "%d-%s-%s %s:%s:00" % (now.tm_year, format(now.tm_mon), format(now.tm_mday), hour, minute)
        targetTime = time.strptime(targetStr, "%Y-%m-%d %H:%M:%S")
        return now > targetTime

    def makeDecision(self, code, price):
        direction = self.getDirection(code, price)
        logger.info("Direction for %s: %s" % (code, direction))
        global availableMoney
        if direction == 'B':
            buyPrice = self.getBuyPrice(price)
            buyAmount = self.getBuyAmount(price)
            if buyPrice <= 0 or buyAmount <= 0:
                return
            if self.operation.order(code, direction, buyPrice, buyAmount):
                if code not in stock_positions:
                    stock_positions[code] = 0
                stock_positions[code] += buyAmount
                availableMoney -= buyPrice * buyAmount
                stock_ordered.append(code)
                logger.info("current availabeMoney = %d, stock_ordered = %s, stock_positions = %s"
                             % (availableMoney, stock_ordered, stock_positions))
        elif direction == 'HS' or direction == 'FS':
            sellPrice = self.getSellPrice(price)
            sellAmount = self.getSellAmount(code)
            if direction == 'FS':
                sellAmount = stock_positions[code]
            if self.operation.order(code, 'S', sellPrice, sellAmount):
                stock_positions[code] -= sellAmount
                availableMoney += sellAmount * sellPrice
                stock_ordered.append(code)
                logger.info("current availabeMoney = %d, stock_ordered = %s, stock_positions = %s"
                             % (availableMoney, stock_ordered, stock_positions))

    def getRealTimeData(self, code):
        df = ts.get_realtime_quotes(code)
        price = df['price'][0]
        # logger.info("Realtime data of %s: %s" %(code, price))
        return float(price)

    def getHistoryDayKAvgData(self, code, days):
        df = ts.get_hist_data(code)
        total = 0.0
        i = 0
        while i < days:
            total += df['close'][i]
            i += 1
        avg = total/days
        logger.info("Historical %d avg data of %s: %f" % (days, code, avg))
        return float(avg)

    def getDirection(self, code, price):
        avg1 = float(self.avg1[code])
        avg10 = float(self.avg10[code])
        avg20 = float(self.avg20[code])
        price = float(price)
        logger.info("%s status: %f, %f, %f, %f" % (code, price, avg1, avg10, avg20))

        if code in stock_ordered:
            # 控制当日单只股票操作次数
            return 'N'

        if code in stock_positions:
            # 控制单只股票市值
            position = stock_positions[code] * price
            if position > maxMoneyPerStock:
                return 'N'

        if code in stock_positions and avg10 * (1-sellThreshold) < price and price < avg10 and avg10 < avg1:
            # 股价跌破10日均值，卖半仓
            return 'HS'

        if code in stock_positions and avg20 * (1-sellThreshold) < price and price < avg20 and avg20 < avg1 and  avg20 < avg10:
            # 股价跌破20日均值，卖全仓
            return 'FS'

        if avg1 < avg10 and avg10 < price and  price < avg10 * (1+buyThreshold):
            # 股价突破10日均值
            return 'B'

        return 'N'

    def getBuyPrice(self, price):
        return price * 1.02

    def getSellPrice(self, price):
        return price * 0.98

    def getBuyAmount(self, price):
        return math.floor(min(maxMoney, availableMoney)/price/100) * 100

    def getSellAmount(self, code):
        return math.ceil(stock_positions[code]/2/100) * 100

class MainGui:
    def __init__(self):
        logger.info("Trying to init MainGui ...")

if __name__ == '__main__':
    # operation = OperationOfThs()
    # operation.getPosition()

    t1 = threading.Thread(target=MainGui)
    t1.start()
    t2 = threading.Thread(target=Monitor)
    t2.start()
