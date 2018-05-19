#/bin/env python

import logging
import math
import operator
import threading
import time
import random
import tkinter.messagebox
from datetime import datetime

import pytz
import pywinauto
import pywinauto.application
import pywinauto.clipboard
import tushare as ts
from pywinauto import keyboard
from pywinauto import mouse
from pywinauto import win32defines
from pywinauto.win32functions import SetForegroundWindow, ShowWindow
from timezone_logging.timezone_logging import get_timezone_logger

from email_sender import sendEmail

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../../logs/auto_deal_ths.log',
                    filemode='a')
logger = get_timezone_logger('auto_deal', fmt="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s", log_level=logging.DEBUG)


stock_codes = ['002647']
stock_positions = {}
stock_chenbens = {}
stock_ordered = []
stock_exception = []
maxMoney = 10000
maxMoneyPerStock = 20000
availableMoney = 10000
sleepTime = 0.5
monitorInterval = 10
sellThreshold = 0.04
buyThreshold = 0.02  # [1-threshold ~ 1+threshold]
zhiYingDian = 1.08 # 止盈点%8
avg10Days = 12 #参考均线天数，默认为10，可以根据具体情况手动调整，一般为10到20

def readCodes():
    global stock_codes
    stock_codes = []
    for code in list(open("codes.txt")):
        stock_codes.append(code.strip())
    logger.info("Monitor codes: %s" % stock_codes)

def getCodesFromNet():
    global stock_codes
    stock_codes = []
    fs = ts.get_stock_basics()
    for code in fs.index:
        if code < '300000' or code >= '600000':
            stock_codes.append(code)

class OperationOfThs:
    def __init__(self):
        logger.info("Init THS operations ...")
        self.__app = pywinauto.application.Application()
        self.screenshotCount = 1
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
        time.sleep(4 * sleepTime)  # wait for popup window to appear
        while self.__closePopupWindow():
            time.sleep(4 * sleepTime)

    def __closePopupWindow(self):
        # logger.info("Closing popup window")
        popup_window = self.__main_window.PopupWindow()
        if popup_window:
            popup_window = self.__app.window_(handle=popup_window)
            popup_window.SetFocus()
            popup_window.Button.Click()
            return True
        return False

    def getChenben(self):
        position = self.__getCleanedData()
        for index in range(1, len(position)):
            code = position[index][1]
            chenben = position[index][7]
            stock_chenbens[code] = float(chenben)

        logger.info("Chenbens: %s" % stock_chenbens)
        if len(stock_chenbens) <= 0:
            logger.error("Failed to get current chenben")
            exit(1)

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
        data = pywinauto.clipboard.GetData() # Copy from clipboard directly after manual copy
        lst = data.strip().split("\r\n")
        matrix = []
        for i in range(0, len(lst)):
            subList = lst[i].split("\t")
            matrix.append(subList)

        # self.minWindow()
        return matrix

    def order(self, code, direction, price, quantity):
        logger.info("Trying to order: [%s - %s - %.2f - %d]" % (code, direction, price, quantity))
        try:
            self.restoreWindow()

            price = "%.2f" % price
            if direction == 'B':
                self.__buy(code, price, quantity)
            if direction == 'S':
                self.__sell(code, price, quantity)
            self.__closePopupWindows()
            # self.minWindow()
            self.saveScreenshot("Ordered: [%s - %s - %.2f - %d]" % (code, direction, float(price), quantity))
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

    def restoreWindow(self):
        if self.__main_window.HasStyle(win32defines.WS_MINIMIZE): # if minimized
            ShowWindow(self.__main_window.wrapper_object(), 9) # restore window state
        else:
            SetForegroundWindow(self.__main_window.wrapper_object()) # bring to front

    def moveMouse(self):
        mouse.move(coords=(random.randint(0,99), random.randint(0, 99)))

    def saveScreenshot(self, status):
        try:
            picName = "../../logs/auto_deal_%s.png" % datetime.now().strftime("%Y-%m-%d_%H-%M")
            self.restoreWindow()
            keyboard.SendKeys("{F4}")
            time.sleep(sleepTime)
            keyboard.SendKeys("{F5}")
            time.sleep(sleepTime)
            self.__main_window.CaptureAsImage().save(picName)
            time.sleep(sleepTime)
            self.screenshotCount += 1
            # pywinauto.application.Application().connect(title = "auto_deal_THS.py").top_window().CaptureAsImage().save(picName)
            sendEmail([picName], status)
        except Exception as e:
            logger.error("Failed to send email: %s" % e)

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

        time.sleep(10)
        self.testSellBeforeDeal()
        time.sleep(5)
        self.testBuyBeforeDeal()

        self.operation.getPosition() # 开盘前获取持仓情况
        self.operation.getChenben() # 开盘前获取成本情况

        global stock_codes
        for code in stock_positions:
            if code not in stock_codes:
                # make sure all stocks within current position are monitored
                stock_codes.append(code)

        start_time = time.time()
        stock2changes = {}
        for code in stock_codes:
            # 需要45分钟更新所有均值 - 近2800支股票
            # 因此需要7点半前开机启动
            p_changes = []
            avg = self.getHistoryDayKAvgData(code, 1, p_changes)
            self.avg1[code] = avg
            stock2changes[code] = p_changes[0]

            avg = self.getHistoryDayKAvgData(code, avg10Days)
            self.avg10[code] = avg

            avg = self.getHistoryDayKAvgData(code, 2 * avg10Days)
            self.avg20[code] = avg
        end_time = time.time()
        self.operation.saveScreenshot("均值更新完成，共耗时%d秒，排除异常，可监控%d支股票" % ((end_time - start_time), (len(stock_codes) - len(stock_exception))))
        # logger.info("Avgs 1: %s" % self.avg1)
        # logger.info("Avgs 10: %s" % self.avg10)
        # logger.info("Avgs 20: %s" % self.avg20)
        stock_codes = self.sortStocks(stock2changes)
        stock_codes_reversed = self.sortStocks(stock2changes, True)
        # logger.info("stock scores: %s" % stock2changes)
        # logger.info("sorted codes: %s" % stock_codes)
        # logger.info("reverse sorted codes: %s" % stock_codes_reversed)
        logger.info("Total monitor code size: %d, exception code size: %d" % (len(stock_codes), len(stock_exception)))

        isStarted = False
        while True:
            try:
                self.operation.moveMouse()

                # if self.compare("14", "55"):
                #     logger.info("Closed deal. Exit.")
                #     break

                if (self.compare("09", "32") and not self.compare("11", "28")) or (self.compare("13", "02") and not self.compare("14", "58")):
                    # 交易时间：[09:30 ~ 11:30, 13:00 ~ 15:00]
                    if not isStarted:
                        self.operation.saveScreenshot("开始交易")
                    isStarted = True
                else:
                    if isStarted:
                        self.operation.saveScreenshot("停止交易")
                    isStarted = False


                time.sleep(monitorInterval)
                if not isStarted:
                    continue

                print()
                logger.debug("looping monitor stocks")

                stock2changes = {}
                # firstly, loop codes in stock_positions, finding out codes that can be sold
                for code in stock_codes:
                    if code in stock_positions:
                        try:
                            p_changes = []
                            price = self.getRealTimeData(code, p_changes)
                            stock2changes[code] = p_changes[0]
                            self.makeDecision(code, price)
                        except Exception as e:
                            logger.error("Failed to monitor %s: %s" % (code, e))

                # secondly, loop other codes, 优先选择当前涨幅大的股票进行买入操作
                # 全部扫描完一遍需要2分钟左右，共1500支左右股票
                for code in stock_codes_reversed:
                    if code not in stock_positions:
                        try:
                            p_changes = []
                            price = self.getRealTimeData(code, p_changes)
                            stock2changes[code] = p_changes[0]
                            self.makeDecision(code, price)
                        except Exception as e:
                            logger.error("Failed to monitor %s: %s" % (code, e))

                stock_codes = self.sortStocks(stock2changes)
                stock_codes_reversed = self.sortStocks(stock2changes, True)
                # logger.debug("sorted codes: %s" % stock_codes)
                # logger.debug("reverse sorted codes: %s" % stock_codes_reversed)
                logger.debug("stock_orders = %s, stock_positions = %s" % (stock_ordered, stock_positions))
            except Exception as e:
                logger.error("Exception happen within loop: %s" % e)

    def formatDate(self, num):
        if num < 10:
            return "0%d" % num
        else:
            return "%d" % num


    def compare(self, hour, minute):
        tz = pytz.timezone('Hongkong')
        now = datetime.now(tz)
        targetStr = "%d-%s-%s %s:%s:00" % (now.year, self.formatDate(now.month), self.formatDate(now.day), hour, minute)
        targetTime = tz.localize(datetime.strptime(targetStr, "%Y-%m-%d %H:%M:%S"))
        return now > targetTime

    def makeDecision(self, code, price):
        direction = self.getDirection(code, price)
        logger.debug("Direction for %s: %s" % (code, direction))
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

    def getRealTimeData(self, code, p_changes = []):
        df = ts.get_realtime_quotes(code)
        price = df['price'][0]
        changePercentage = (float(df['price'][0]) - float(df['pre_close'][0])) / float(df['pre_close'][0])  * 100
        p_changes.append(self.formatFloat(changePercentage))
        logger.debug("Realtime data of %s: %s" %(code, price))
        return float(price)

    def formatFloat(self, number):
        str = "%.2f" % number
        return float(str)

    def getHistoryDayKAvgData(self, code, days, p_changes = []):
        df = ts.get_hist_data(code)
        total = 0.0
        i = 0
        try:
            while i < days and 'close' in df:
                total += df['close'][i]
                p_changes.append(df['p_change'][i])
                i += 1
        except Exception as e:
            logger.error("Error while get code %s: %s" % (code, e))
            p_changes.append(0)
            stock_exception.append(code)
        avg = self.formatFloat(total/days)
        logger.debug("Historical %d avg data of %s: %.2f" % (days, code, avg))
        return avg

    def getDirection(self, code, price):
        avg1 = float(self.avg1[code])
        avg10 = float(self.avg10[code])
        avg20 = float(self.avg20[code])
        price = float(price)
        logger.info("%s status: %f, %f, %f, %f" % (code, price, avg1, avg10, avg20))

        if code in stock_ordered or code in stock_exception:
            # 控制当日单只股票操作次数, 监控异常
            return 'N'

        if avg1 * 0.99 < price and price < avg1 * 1.01:
            # 如果股价波动过小，则不操作
            return 'N'

        if code in stock_chenbens and price > stock_chenbens[code] * zhiYingDian:
            # 设置止盈点10%
            return 'FS'

        if code in stock_positions and avg10 * (1-sellThreshold) < price and price < avg10 and avg10 < avg1:
            # 股价跌破10日均值，卖半仓
            return 'HS'

        if code in stock_positions and avg20 * (1-sellThreshold) < price and price < avg20 and avg20 < avg1 and  avg20 < avg10:
            # 股价跌破20日均值，卖全仓
            return 'FS'

        if code in stock_positions:
            # 控制单只股票市值
            position = stock_positions[code] * price
            if position > maxMoneyPerStock:
                return 'N'

        if avg1 < avg10 and avg10 < price and  price < avg10 * (1+buyThreshold):
            # 股价突破10日均值
            return 'B'

        return 'N'

    def sortStocks(self, stock2score, reverse = False):
        sortedCodes = sorted(stock2score.items(), key=operator.itemgetter(1), reverse = reverse)
        codes = []
        for i in range(0, len(sortedCodes)):
            codes.append(sortedCodes[i][0])
        return codes

    def getBuyPrice(self, price):
        return price * 1.02

    def getSellPrice(self, price):
        return price * 0.98

    def getBuyAmount(self, price):
        amount = math.floor(min(maxMoney, availableMoney)/price/100) * 100
        if amount * price < 5000:
            amount = 0
        return amount

    def getSellAmount(self, code):
        return math.ceil(stock_positions[code]/2/100) * 100

class MainGui:
    def __init__(self):
        logger.info("Trying to init MainGui ...")

if __name__ == '__main__':
    # readCodes()
    getCodesFromNet()

    t1 = threading.Thread(target=MainGui)
    t1.start()
    t2 = threading.Thread(target=Monitor)
    t2.start()
