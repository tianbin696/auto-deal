#/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import random
import numpy
import os
from datetime import datetime
from datetime import timedelta

import pytz
import pywinauto
import pywinauto.application
import pywinauto.clipboard
import tushare as ts
import pandas as pd
from pywinauto import keyboard
from pywinauto import mouse
from pywinauto import win32defines
from pywinauto.win32functions import SetForegroundWindow, ShowWindow

from email_sender import sendEmail
from yan_zhen_ma import get_vcode
from tong_hua_shun import ths_start
from tong_hua_shun import ths_close
from stats import get_code_filter_list
from stats import var
from stats import sort_codes
from macd import get_MACD

from tushare_api import TushareAPI
local_ts = TushareAPI()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../../logs/auto_deal_ths.log',
                    filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
console.setFormatter(formatter)
logger = logging.getLogger('auto_deal')
logger.addHandler(console)
stock_codes = []
new_codes = []
ignore_codes = []
stock_positions = {}
stock_chenbens = {}
maxCodeSize = 1 # 最大持股数
globalAvailableMoney = 20000
maxAmount = 30000
minAmount = 0
minBuyAmount = 6000
sleepTime = 0.5
monitorInterval = 60
avg10Days = 10 #参考均线天数，默认为10，可以根据具体情况手动调整，一般为10到20
cache = {}

def readCodes():
    global new_codes
    timeStr = time.strftime("%Y%m%d", time.localtime())
    filePath = "../codes/candidates.txt"
    new_codes = []
    if os.path.exists(filePath):
        for code in list(open(filePath)):
            new_codes.append(code.strip())
    logger.info("Monitor codes: %s" % new_codes)


class OperationOfThs:
    def __init__(self):
        logger.info("Init THS operations ...")
        self.__app = pywinauto.application.Application()
        self.screenshotCount = 1
        try:
            self.__app.connect(title = u'网上股票交易系统5.0')
            top_window = pywinauto.findwindows.find_window(title=u'网上股票交易系统5.0')
            dialog_window = pywinauto.findwindows.find_windows(top_level_only=False, class_name='#32770', parent=top_window)[0]
            wanted_window = pywinauto.findwindows.find_windows(top_level_only=False, parent=dialog_window)

            if len(wanted_window) == 0:
                tkinter.messagebox.showerror('错误', '无法获得“同花顺双向委托界面”的窗口句柄,请将同花顺交易系统切换到“双向委托界面”！')
                exit()

            self.__main_window = self.__app.window_(handle=top_window)
            self.__dialog_window = self.__app.window_(handle=top_window)
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

        self.__dialog_window[u'买入Button'].Click()
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

        self.__dialog_window.child_window(title=u"卖出", class_name="Button").Click()
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
        self.restoreWindow()
        self.__init__()
        self.__dialog_window.CVirtualGridCtrl.RightClick(coords=(30, 30))
        self.__main_window.TypeKeys('C')
        time.sleep(sleepTime)
        popup_window = self.__main_window.PopupWindow()
        if popup_window:
            popup_window = self.__app.window_(handle=popup_window)
            popup_window.CaptureAsImage().save("v_code.png")
            vcode = get_vcode('v_code.png')
            popup_window.SetFocus()
            popup_window.Edit.SetFocus()
            time.sleep(sleepTime)
            popup_window.Edit.SetEditText(vcode)
            time.sleep(sleepTime)
            popup_window.child_window(title=u"确定", class_name="Button").Click()

        data = pywinauto.clipboard.GetData() # Copy from clipboard directly after manual copy
        lst = data.strip().split("\r\n")
        matrix = []
        for i in range(0, len(lst)):
            subList = lst[i].split("\t")
            matrix.append(subList)

        # self.minWindow()
        return matrix

    def order(self, code, direction, price, quantity):
        chenben = 0.0
        if code in stock_chenbens:
            chenben = stock_chenbens[code]
        logger.info("Trying to order: [%s - %s - %.2f - %d - 成本:%.2f]" % (code, direction, price, quantity, chenben))
        try:
            self.restoreWindow()
            self.__closePopupWindows()

            price = "%.2f" % price
            if direction == 'B':
                self.__buy(code, price, quantity)
            if direction == 'S':
                self.__sell(code, price, quantity)
            self.__closePopupWindows()
            # self.minWindow()
            self.saveScreenshot("Ordered: [%s - %s - %.2f - %d - 成本:%.2f]" % (code, direction, float(price), quantity, chenben), u'操作：%s' % direction)
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

    def saveScreenshot(self, status, title):
        try:
            self.__closePopupWindows()
            picName = "../../logs/auto_deal_%s.png" % datetime.now().strftime("%Y-%m-%d_%H-%M")
            self.restoreWindow()
            keyboard.SendKeys("{F4}")
            time.sleep(2*sleepTime)
            keyboard.SendKeys("{F5}")
            time.sleep(2*sleepTime)
            keyboard.SendKeys("{F5}")
            time.sleep(2*sleepTime)
            self.__main_window.CaptureAsImage().save(picName)
            time.sleep(sleepTime)
            self.screenshotCount += 1
            sendEmail([picName], status, title)
        except Exception as e:
            logger.error("Failed to send email: %s" % e)

class Monitor:

    def __init__(self):
        logger.info("Trying to Init monitor ...")
        self.avg1 = {}
        self.avg5 = {}
        self.avg10 = {}
        self.avg20 = {}
        self.liangBi5 = {}
        self.volumeAvg5 = {}
        self.rsis = {}
        self.macds = {}
        self.isBuyeds = {}
        self.isSelleds = {}
        self.buyedPrices = {}
        self.selledPrices = {}
        self.availableMoney = globalAvailableMoney
        self.operation = OperationOfThs()

    def testSellBeforeDeal(self):
        self.operation.order('600570', 'S', 0, 200)

    def testBuyBeforeDeal(self):
        self.operation.order('600570', 'B', 0, 200)

    def loopMonitor(self):
        logger.info("Start loop monitor ...")

        time.sleep(5)
        self.testBuyBeforeDeal()

        self.operation.getPosition() # 开盘前获取持仓情况
        self.operation.getChenben() # 开盘前获取成本情况

        for code in stock_positions.keys():
            if code not in stock_codes:
                stock_codes.append(code)

        for code in new_codes:
            if code not in stock_codes:
                stock_codes.append(code)

        start_time = time.time()
        for code in stock_codes:
            p_changes = []
            avg = self.getHistoryDayKAvgData(code, 1, p_changes)
            self.avg1[code] = avg

            avg = self.getHistoryDayKAvgData(code, int(avg10Days/2), p_changes)
            self.avg5[code] = avg

            avg = self.getHistoryDayKAvgData(code, avg10Days)
            self.avg10[code] = avg

            avg = self.getHistoryDayKAvgData(code, 2 * avg10Days)
            self.avg20[code] = avg

            self.liangBi5[code] = self.getLiangBi(code, int(avg10Days/2))
            self.volumeAvg5[code] = self.getVolumeAvg(code, int(avg10Days/2))

        temp_arr = []
        for code in stock_codes:
            if self.avg10[code][0] > 0:
                temp_arr.append(code)

                ndf = cache[code]['close'][0:20].reset_index()
                rsi6 = getRSI(ndf['close'], 6)
                rsi12 = getRSI(ndf['close'], 12)
                self.rsis[code] = "%d-%d" % (rsi6, rsi12)
                logger.info("RSI of %s: %d-%d" % (code, rsi6, rsi12))

                macd = self.getRealTimeMACD(code, self.avg1[code][0])
                self.macds[code] = float("%.2f" % macd[0])
                logger.info("macd of %s: %.2f" % (code, macd[0]))
        stock_codes.clear()
        yesterday = (datetime.now() - timedelta(days = 1))
        timeStr = yesterday.strftime("%Y%m%d")
        # stock_codes.extend(sort_codes(temp_arr, avg10Days, timeStr))
        stock_codes.extend(temp_arr)
        end_time = time.time()
        self.operation.saveScreenshot("均值更新完成，共耗时%d秒，排除异常，可监控%d支股票。"
                                      "avg1=%s, macd=%s, rsi=%s, new_codes=%s" % ((end_time - start_time), len(stock_codes),
                                                                       self.avg1, self.macds, self.rsis, new_codes), u'交易前准备')
        logger.info("Total monitor code size: %d. Codes=%s" % (len(stock_codes), stock_codes))

        isStarted = False
        totalSleep = 0
        while True:
            try:
                self.operation.moveMouse()

                if (self.compare("09", "35") and not self.compare("11", "28")) or (self.compare("13", "02") and not self.compare("14", "58")):
                    # 交易时间：[09:30 ~ 11:30, 13:00 ~ 15:00]
                    if not isStarted:
                        self.operation.saveScreenshot("开始交易", '开始交易')
                    isStarted = True
                else:
                    if isStarted:
                        self.operation.saveScreenshot("停止交易", '停止交易')
                    isStarted = False

                if self.compare("15", "00"):
                    logger.info("Closed deal. Exit.")
                    break

                time.sleep(monitorInterval)
                totalSleep += monitorInterval
                if totalSleep > 3600:
                    totalSleep = 0
                    # self.operation.saveScreenshot("状态更新", '状态更新')

                if not isStarted:
                    continue

                if not self.compare("14", "30"):
                    continue

                print()
                logger.debug("looping monitor stocks")

                #stock_codes.clear()
                #stock_codes.append('002797')
                for code in stock_codes:
                    try:
                        if code in ignore_codes or self.avg10[code][0] <= 0:
                            continue
                        p_changes = []
                        open_prices = []
                        highest_prices = []
                        lowest_price = []
                        volumes = []
                        price = self.getRealTimeData(code, p_changes, open_prices, highest_prices, lowest_price, volumes)
                        self.makeDecision(code, price, open_prices[0], p_changes[0], highest_prices[0], lowest_price[0], volumes[0])
                    except Exception as e:
                        logger.error("Failed to monitor %s: %s" % (code, e))

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

    def makeDecision(self, code, price, open_price, change_p, highest_price, lowest_price, volume):
        chen_ben = 0
        if code in stock_chenbens:
            chen_ben = stock_chenbens[code]
        direction = self.getDirection(code, price, open_price, highest_price, lowest_price, chen_ben, volume)
        logger.info("Direction for %s: %s" % (code, direction))
        if direction == 'B':
            if self.availableMoney < minBuyAmount:
                return
            if code in stock_positions and stock_positions[code]*price + minBuyAmount >= maxAmount:
                # 达到持仓上限，不再买入
                logger.info("Reach max amount, cannot buy anymore")
                return
            buyPrice = self.getBuyPrice(price)
            if buyPrice <= 0:
                return
            buyAmount = self.getBuyAmount(code, price)
            self.isBuyeds[code] = True
            if self.operation.order(code, direction, buyPrice, buyAmount):
                if code not in stock_positions:
                    stock_positions[code] = 0
                self.isBuyeds[code] = True
                self.buyedPrices[code] = price
                self.availableMoney -= buyAmount*price
        elif direction == 'S' or direction == 'FS':
            if code not in stock_positions or stock_positions[code]*price <= minAmount:
                # 达到持仓下限，不再卖出
                logger.info("Reach min amount, cannot sell anymore")
                return
            sellPrice = self.getSellPrice(price)
            if float(change_p) < -9.0:
                # 无法计算跌停价时以现价卖出
                sellPrice = price
            if float(change_p) < -8.0 and float(change_p) >= -9.0:
                sellPrice = price * 0.99
            if sellPrice <= 0:
                return
            sellAmount = self.getSellAmount(code, price)
            if direction == 'FS':
                sellAmount = stock_positions[code]
            self.isSelleds[code] = True
            if self.operation.order(code, 'S', sellPrice, sellAmount):
                stock_positions[code] -= sellAmount
                if stock_positions[code] <= 0:
                    del stock_positions[code]
                self.isSelleds[code] = True
                self.selledPrices[code] = price

    def getRealTimeData(self, code, p_changes=[], open_prices=[], highest_prices=[], lowest_prices=[], volumes=[]):
        df = ts.get_realtime_quotes(code)
        price = df['price'][0]
        changePercentage = (float(df['price'][0]) - float(df['pre_close'][0])) / float(df['pre_close'][0])  * 100
        open_prices.append(float(df['open'][0]))
        highest_prices.append(float(df['high'][0]))
        lowest_prices.append(float(df['low'][0]))
        volumes.append(int(df['volume'][0]))
        p_changes.append(self.formatFloat(changePercentage))
        logger.debug("Realtime data of %s: %s" %(code, price))
        return float(price)

    def formatFloat(self, number):
        str = "%.2f" % number
        return float(str)

    def getHistoryDayKAvgData(self, code, days, p_changes = []):
        if code in cache:
            df = cache[code]
        else:
            retry = 10
            logger.info("Getting historical data for code: %s" % code)
            while retry > 0:
                try:
                    yesterday = (datetime.now() - timedelta(days = 1))
                    timeStr = yesterday.strftime("%Y%m%d")
                    df = ts.get_h_data(code, pause=10)
                    break
                except Exception as e:
                    logger.error("Failed to get history data: %s" % e)
                    time.sleep(60)
                    retry -= 1
            d = {'close':df['close'][0:52].astype('float'), 'high':df['high'][0:52].astype('float'), 'low':df['low'][0:52].astype('float'), 'volume':df['volume'][0:52].astype('int')}
            ndf = pd.DataFrame(d)

            # Extend df
            rtDF = ts.get_realtime_quotes(code)
            nd2 = {'close':rtDF['price'][0:1].astype('float'), 'high':rtDF['high'][0:1].astype('float'), 'low':rtDF['low'][0:1].astype('float'), 'volume':rtDF['volume'][0:1].astype('float')}
            ndf2 = pd.DataFrame(nd2)

            df = pd.concat([ndf2, ndf]).reset_index()
            cache[code] = df
        avgs = []
        try:
            if 'close' in df:
                for i in range(days):
                    avg = numpy.mean(df['close'][i+1:i+days+1])
                    avg = float("%.2f" % avg)
                    avgs.append(avg)
                p_changes.append(0)
        except Exception as e:
            logger.error("Error while get code %s: %s" % (code, e))
            p_changes.append(0)
        logger.debug("Historical %d avg data of %s: %s" % (days, code, avgs))
        print("Historical %d avg data of %s: %s" % (days, code, avgs))
        return avgs

    def getLiangBi(self, code, days=5):
        result = []
        df = cache[code]
        for i in range(days):
            result.append(float("%.2f" % (df['volume'][i+1]/numpy.mean(df['volume'][i+1:i+1+days]))))
        logger.info("%s days LiangBi of %s: %s" % (days, code, result))
        return result

    def getVolumeAvg(self, code, days=5):
        result = []
        df = cache[code]
        for i in range(days):
            result.append(int(numpy.mean(df['volume'][i+1:i+1+days])))
        logger.info("%s days Volume avg of %s: %s" % (days, code, result))
        return result

    def getRealTimeMACD(self, code, price):
        cache[code].update(pd.DataFrame({'close':[price]}, index=[0]))
        cache[code] = get_MACD(cache[code],12,26,9)
        return cache[code]['macd']

    def getDirection(self, code, price, open_price, highest_price, lowest_price, chen_ben=0, volume=0):
        # 理论基础：趋势一旦形成，短期不会改变
        avg1 = float(self.avg1[code][0])
        avg5 = self.avg5[code]
        avg10 = self.avg10[code]
        avg20 = self.avg20[code]
        price = float(price)
        volumeAvg5 = self.volumeAvg5[code]
        liangBi5 = self.liangBi5[code]
        df = cache[code]
        liangBi = float("%.2f" % (volume/volumeAvg5[0]))
        logger.info("%s status: price=%f, highest_price=%f, lowest_price=%f, avg1=%f, avg10=%f, avg20=%f, liangBi=%s" %
                    (code, price, highest_price, lowest_price, avg1, avg10[0], avg20[0], liangBi))
        if price <= 0:
            return 'N'

        # 顺势下跌，卖出
        if code not in self.isSelleds or not self.isSelleds[code]:
            if (code not in self.isBuyeds or not self.isBuyeds[code]) \
                    and price > numpy.max(df['close'][1:11])*0.8 \
                    and avg5[0] < min(avg5[1], avg5[2]):
                if price < avg1*0.96:
                    if code in stock_positions and stock_positions[code]*price < 5000:
                        return 'FS'
                    return 'S'

        # 顺势上涨，买入
        if code not in self.isBuyeds or not self.isBuyeds[code]:
            if (code not in self.isSelleds or not self.isSelleds[code]) \
                    and price < numpy.min(df['close'][1:11])*1.2 \
                    and avg5[0] > max(avg5[1], avg5[2]) \
                    and code in new_codes:
                if max(avg1*1.02, highest_price*0.96) < price < avg1*1.06:
                        return 'B'

        return 'N'

    def getBuyPrice(self, price):
        return price * 1.01

    def getSellPrice(self, price):
        return price * 0.99

    def getBuyAmount(self, code, price):
        return int(minBuyAmount/100/price)*100

    def getSellAmount(self, code, price):
        return max(int(stock_positions[code]/200)*100, 100)


def getRSI(prices, days=8):
    positiveSum = 0
    positiveCount = 0
    negativeSum = 0
    negativeCount = 0
    totalSum = 0
    for i in range(0, days):
        increase = (prices[i] - prices[i+1])/prices[i+1]
        if increase > 0:
            positiveSum += increase
            positiveCount += 1
        else:
            negativeSum += increase
            negativeCount += 1
    result = ((positiveSum)*100) / ((positiveSum + abs(negativeSum)))
    return int(result)

def test():
    monitor = Monitor()

    # Test before start
    test_codes = ["601788", "002673"]
    # test_codes.extend(["002797", "002673", "601066", "600958", "601198", "000686", "002670", "600061", "600864", "601788"])
    # test_codes.extend(["002195", "600718", "600446", "600536", "600797", "002657", "600571", "600588", "600756", "002777"])
    for code in test_codes:
        price = monitor.getHistoryDayKAvgData(code, 1)
        real_volume = []
        price = monitor.getRealTimeData(code, volumes=real_volume)
        df = cache[code]
        v5 = numpy.mean(df['volume'][1:6])
        v10 = numpy.mean(df['volume'][1:11])
        volume = numpy.mean([v5, v10])
        logger.info("code=%s, v5=%s, v10=%s, vm=%s" % (code, v5, v10, volume))
        monitor.avg1[code] = monitor.getHistoryDayKAvgData(code, 1)
        monitor.avg5[code] = monitor.getHistoryDayKAvgData(code, 5)
        monitor.avg10[code] = monitor.getHistoryDayKAvgData(code, 10)
        monitor.avg20[code] = monitor.getHistoryDayKAvgData(code, 20)
        monitor.liangBi5[code] = monitor.getLiangBi(code, 5)
        monitor.volumeAvg5[code] = monitor.getVolumeAvg(code, 5)
        df = cache[code]
        #  测试卖出
        highest_close = numpy.max(df['close'][1:25])
        direction = monitor.getDirection(code, price*0.94, price*1.05, price*1.05, price*0.98, price, volume*1.01)
        logger.info("code=%s, direction=%s" % (code, direction))
        stock_positions[code] = 5500/(price*0.94)
        direction = monitor.getDirection(code, price*0.925, price*1.0, price*1.05, price*0.98, price, volume*1.01)
        logger.info("code=%s, direction=%s" % (code, direction))
        stock_positions[code] = 4500/(price*0.94)
        direction = monitor.getDirection(code, price*0.93, price*1.0, price*1.15, price*0.98, price, volume*1.01)
        logger.info("code=%s, direction=%s" % (code, direction))
        stock_positions.clear()
        # 测试买入
        global new_codes
        minest_close = numpy.min(df['close'][1:25])
        direction = monitor.getDirection(code, price*1.025, price, price*1.04, price*0.98, price, volume*1.01)
        logger.info("code=%s, direction=%s" % (code, direction))
        new_codes.append(code)
        direction = monitor.getDirection(code, price*1.025, price, price*1.04, price*0.98, price, volume*1.01)
        logger.info("code=%s, direction=%s" % (code, direction))
        new_codes = []
        cache.clear()


if __name__ == '__main__':
    readCodes()
    test()

    while True:
        try:
            wday = time.localtime().tm_wday
            if wday > 4:
                logger.info("Sleep before monitor, current_wday=%d" % wday)
                time.sleep(3600)
                continue
            
            hour = time.localtime().tm_hour
            if hour < 7 or hour >= 15:
                logger.info("Sleep before monitor, current_hour=%d" % hour)
                time.sleep(60)
                # if hour == 18:
                #     get_code_filter_list(avg10Days, "codes.txt")
                #     time.sleep(3600)
                continue

            time.sleep(60)
            ths_start()

            cache.clear()
            stock_codes.clear()
            stock_positions.clear()
            readCodes()
            ignore_codes.extend([])
            
            monitor = Monitor()
            logger.info("Testing ...")
            time.sleep(5)
            monitor.testSellBeforeDeal()

            monitor.loopMonitor()

            # get_code_filter_list(avg10Days, "codes.txt", timeStr=None)

            logger.info("Close THS after deal")
            time.sleep(120)
            ths_close()
        except Exception as e:
            logger.error("Error happen: %s" % e)
            ths_close()
