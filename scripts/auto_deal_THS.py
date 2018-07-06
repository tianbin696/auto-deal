#/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import random
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

from email_sender import sendEmail
from yan_zhen_ma import get_vcode
from tong_hua_shun import ths_start
from tong_hua_shun import ths_close

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
# 精选不同行业个股（汽车零部件，化工新材料，银行，计算机应用，零售，饮料制造，化学制药，医药商业，国防军工, 白色家电，有色冶炼，建筑材料，房地产，农业服务，物流），分散投资，降低风险
# 福耀玻璃，石大胜华，上海银行，东华软件，苏宁易购，张裕A，济川药业，瑞康医药，中兵红箭，青岛海尔，天齐锂业，华新水泥，招商蛇口，生物股份，韵达股份
stock_codes = ['600660', '603026', '601229', '002065', '002024', '000869', '600566', '002589', '000519', '600690',
               '002466', '600801', '001979', '600201', '002120']
ignore_codes = ['002065']
stock_positions = {}
stock_chenbens = {}
isBuyeds = {}
isSelleds = {}
maxAmount = 30000
minAmount = 0
minBuyAmount = 10000
minSellAmount = 10000
sleepTime = 0.5
monitorInterval = 10
avg10Days = 12 #参考均线天数，默认为10，可以根据具体情况手动调整，一般为10到20

def readCodes():
    global stock_codes
    stock_codes = []
    for code in list(open("codes.txt")):
        stock_codes.append(code.strip())
    logger.info("Monitor codes: %s" % stock_codes)


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
            self.saveScreenshot("Ordered: [%s - %s - %.2f - %d - 成本:%.2f]" % (code, direction, float(price), quantity, chenben))
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
            self.__closePopupWindows()
            picName = "../../logs/auto_deal_%s.png" % datetime.now().strftime("%Y-%m-%d_%H-%M")
            self.restoreWindow()
            keyboard.SendKeys("{F4}")
            time.sleep(2*sleepTime)
            keyboard.SendKeys("{F5}")
            time.sleep(2*sleepTime)
            self.__main_window.CaptureAsImage().save(picName)
            time.sleep(sleepTime)
            self.screenshotCount += 1
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

        start_time = time.time()
        for code in stock_codes:
            p_changes = []
            avg = self.getHistoryDayKAvgData(code, 1, p_changes)
            self.avg1[code] = avg

            avg = self.getHistoryDayKAvgData(code, avg10Days)
            self.avg10[code] = avg

            avg = self.getHistoryDayKAvgData(code, 2 * avg10Days)
            self.avg20[code] = avg
        end_time = time.time()
        self.operation.saveScreenshot("均值更新完成，共耗时%d秒，排除异常，可监控%d支股票" % ((end_time - start_time), len(stock_codes)))
        logger.info("Total monitor code size: %d" % (len(stock_codes)))

        isStarted = False
        totalSleep = 0
        while True:
            try:
                self.operation.moveMouse()

                if (self.compare("09", "32") and not self.compare("11", "28")) or (self.compare("13", "02") and not self.compare("14", "58")):
                    # 交易时间：[09:30 ~ 11:30, 13:00 ~ 15:00]
                    if not isStarted:
                        self.operation.saveScreenshot("开始交易")
                    isStarted = True
                else:
                    if isStarted:
                        self.operation.saveScreenshot("停止交易")
                    isStarted = False

                if self.compare("15", "00"):
                    logger.info("Closed deal. Exit.")
                    break

                time.sleep(monitorInterval)
                totalSleep += monitorInterval
                if totalSleep % 3600 == 0:
                    self.operation.saveScreenshot("状态更新")

                if not isStarted:
                    continue

                print()
                logger.debug("looping monitor stocks")

                for code in stock_codes:
                    try:
                        if code in ignore_codes:
                            continue
                        p_changes = []
                        open_prices = []
                        highest_prices = []
                        lowest_price = []
                        price = self.getRealTimeData(code, p_changes, open_prices, highest_prices, lowest_price)
                        self.makeDecision(code, price, open_prices[0], p_changes[0], highest_prices[0], lowest_price[0])
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

    def makeDecision(self, code, price, open_price, change_p, highest_price, lowest_price):
        direction = self.getDirection(code, price, open_price, highest_price, lowest_price)
        logger.info("Direction for %s: %s" % (code, direction))
        if direction == 'B':
            if code in stock_positions and stock_positions[code]*price >= maxAmount:
                # 达到持仓上限，不再买入
                logger.info("Reach max amount, cannot buy anymore")
                return
            buyPrice = self.getBuyPrice(price)
            if buyPrice <= 0:
                return
            buyAmount = self.getBuyAmount(code, price)
            if self.operation.order(code, direction, buyPrice, buyAmount):
                # stock_positions[code] += buyAmount
                # 当日买进的仓位无法卖出，所以不计入当日持仓
                isBuyeds[code] = True
        elif direction == 'S':
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
            if self.operation.order(code, 'S', sellPrice, sellAmount):
                stock_positions[code] -= sellAmount
                isSelleds[code] = True

    def getRealTimeData(self, code, p_changes=[], open_prices=[], highest_prices=[], lowest_prices=[]):
        df = ts.get_realtime_quotes(code)
        price = df['price'][0]
        changePercentage = (float(df['price'][0]) - float(df['pre_close'][0])) / float(df['pre_close'][0])  * 100
        open_prices.append(float(df['open'][0]))
        highest_prices.append(float(df['high'][0]))
        lowest_prices.append(float(df['low'][0]))
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
        avg = self.formatFloat(total/days)
        logger.debug("Historical %d avg data of %s: %.2f" % (days, code, avg))
        return avg

    def getDirection(self, code, price, open_price, highest_price, lowest_price):
        avg1 = float(self.avg1[code])
        avg10 = float(self.avg10[code])
        avg20 = float(self.avg20[code])
        price = float(price)
        logger.info("%s status: %f, %f, %f, %f" % (code, price, avg1, avg10, avg20))
        if price <= 0:
            return 'N'

        if code not in isSelleds or not isSelleds[code]:
            if price < highest_price*0.992 and price > avg10*0.94:
                # 只有当股价低于日内最高点时，才考虑卖出，避免卖出持续上涨和一字板的股票
                # 且股价高于10日线*0.94，避免持续卖出大幅下跌的股票

                if price > avg10*1.08 and price > avg1*1.03:
                    # 股价高于10日线8%，止盈
                    return 'S'

                if price > avg1*1.08:
                    # 日涨幅超过8%时，止盈
                    return 'S'

                if price < avg1*0.97 and price < avg10*0.98 and price < open_price:
                    # 当日跌幅超过3%且当前股价低于10日线时，止损
                    return 'S'

        if code not in isBuyeds or not isBuyeds[code]:
            if price < highest_price*0.96:
                # 避免买入高位回落股票
                return 'N'
            if price > avg1*1.02 and price < avg1 * 1.04 and price > open_price and price > avg10 and price < avg10*1.04:
                # 突破10日均线，满足条件的股价区间为[avg10*0.96 ~ avg10*1.01]，共5个点的区间
                return 'B'

            # if price > avg1*1.03 and price < avg1*1.04 and price > open_price and price < avg10*1.04:
            #     # 10日线下反转，买入
            #     return 'B'
            #
            # if price > lowest_price*1.03 and price < avg1*1.04 and price > open_price and price < avg10*1.04:
            #     # 长下影线，反转买入
            #     return 'B'

        return 'N'

    def getBuyPrice(self, price):
        return price * 1.02

    def getSellPrice(self, price):
        return price * 0.98

    def getBuyAmount(self, code, price):
        return int(minBuyAmount/100/price)*100

    def getSellAmount(self, code, price):
        return min(stock_positions[code], int(minSellAmount/100/price)*100)

if __name__ == '__main__':
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
                continue

            time.sleep(30)
            ths_start()

            monitor = Monitor()
            logger.info("Testing ...")
            time.sleep(5)
            monitor.testSellBeforeDeal()

            monitor.loopMonitor()

            logger.info("Close THS after deal")
            time.sleep(120)
            ths_close()
        except Exception as e:
            logger.error("Error happen: %s" % e)
            ths_close()
