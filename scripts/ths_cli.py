#/bin/env python
# -*- coding: utf-8 -*-

import logging
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

import time
import random
from datetime import datetime

import pywinauto
import pywinauto.application
import pywinauto.clipboard
from pywinauto import keyboard
from pywinauto import mouse
from pywinauto import win32defines
from pywinauto.win32functions import SetForegroundWindow, ShowWindow

from yan_zhen_ma import get_vcode
from email_sender import sendEmail


class OperationOfThs:
    def __init__(self):
        self.sleep_time = 0.5
        self.screenshotCount = 1
        self.__app = pywinauto.application.Application()

    def start(self):
        mouse.click(coords=(4000, 4000))
        self.__ths_start()
        try:
            logger.info("connecting THS ...")
            self.__app.connect(title=u'网上股票交易系统5.0')
            logger.info("connected THS")
            top_window = pywinauto.findwindows.find_window(title=u'网上股票交易系统5.0')
            dialog_window = pywinauto.findwindows.find_windows(top_level_only=False, class_name='#32770', parent=top_window)[0]
            wanted_window = pywinauto.findwindows.find_windows(top_level_only=False, parent=dialog_window)

            if len(wanted_window) == 0:
                logger.error("cannot open tong hua shun window")
                exit()
            self.__main_window = self.__app.window(handle=top_window)
            self.__dialog_window = self.__app.window(handle=top_window)
        except Exception as e:
            logger.info("error during init THS: %s" % e)
            exit(1)

    def stop(self):
        self.__ths_close()

    def __ths_start(self):
        mouse.double_click(coords=(40, 40))
        time.sleep(20)
        mouse.click(coords=(1, 1))

    def __ths_restore(self):
        main_window = pywinauto.application.Application().connect(title = u'网上股票交易系统5.0').top_window()
        if main_window.has_style(win32defines.WS_MINIMIZE): # if minimized
            ShowWindow(main_window.wrapper_object(), 9) # restore window state
        else:
            SetForegroundWindow(main_window.wrapper_object()) # bring to front

    def __ths_close(self):
        self.__ths_restore()
        time.sleep(2)
        keyboard.send_keys('%{F4}')

    def __buy(self, code, price, quantity):
        keyboard.send_keys("{F1}")
        time.sleep(self.sleep_time)
        self.__init__()

        # self.__dialog_window.print_control_identifiers()
        self.__dialog_window.Edit0.set_focus()
        time.sleep(self.sleep_time)
        self.__dialog_window.Edit0.set_edit_text(code)
        keyboard.send_keys(code)
        time.sleep(self.sleep_time)

        self.__dialog_window.Edit2.set_focus()
        time.sleep(self.sleep_time)
        self.__dialog_window.Edit2.set_edit_text(price)
        keyboard.send_keys("%s" % price)
        time.sleep(self.sleep_time)

        self.__dialog_window.Edit3.set_focus()
        time.sleep(self.sleep_time)
        self.__dialog_window.Edit3.set_edit_text(quantity)
        keyboard.send_keys("%d" % quantity)
        time.sleep(self.sleep_time)

        self.__dialog_window[u'买入Button'].click()
        time.sleep(self.sleep_time)

    def __sell(self, code, price, quantity):
        keyboard.send_keys("{F2}")
        time.sleep(self.sleep_time)
        self.__init__()

        self.__dialog_window.print_control_identifiers()
        self.__dialog_window.Edit0.set_focus()
        time.sleep(self.sleep_time)
        self.__dialog_window.Edit0.set_edit_text(code)
        keyboard.send_keys(code)
        time.sleep(self.sleep_time)

        self.__dialog_window.Edit2.set_focus()
        time.sleep(self.sleep_time)
        self.__dialog_window.Edit2.set_edit_text(price)
        keyboard.send_keys("%s" % price)
        time.sleep(self.sleep_time)

        self.__dialog_window.Edit3.set_focus()
        time.sleep(self.sleep_time)
        self.__dialog_window.Edit3.set_edit_text(quantity)
        keyboard.send_keys("%d" % quantity)
        time.sleep(self.sleep_time)

        self.__dialog_window[u'卖出Button'].click()
        # self.__dialog_window.child_window(title=u"卖出", class_name="Button").Click()
        time.sleep(self.sleep_time)

    def __closePopupWindows(self):
        logger.info("closing popup windows")
        time.sleep(4 * self.sleep_time)  # wait for popup window to appear
        while self.__closePopupWindow():
            time.sleep(4 * self.sleep_time)

    def __closePopupWindow(self):
        logger.info("closing popup window")
        popup_window = self.__main_window.popup_window()
        if popup_window:
            popup_window = self.__app.window(handle=popup_window)
            popup_window.set_focus()
            popup_window.Button.click()
            return True
        return False

    def getChenben(self):
        position = self.__getCleanedData()
        stock_chenbens = {}
        for index in range(1, len(position)):
            # code = position[index][1].encode() # for VM
            code = position[index][1]
            chenben = position[index][6]
            stock_chenbens[code] = float(chenben)

        logger.info("Chenbens: %s" % stock_chenbens)
        if len(stock_chenbens) <= 0:
            logger.error("failed to get current chenben")
            exit(1)
        return stock_chenbens

    def getPosition(self):
        position = self.__getCleanedData()
        stock_positions = {}
        for index in range(1, len(position)):
            # code = position[index][1].encode() # for VM
            code = position[index][1]
            amount = position[index][3]
            # if position[index][3] != position[index][4]:
            #     amount = 0
            stock_positions[code] = int(amount)

        logger.info("positions: %s" % stock_positions)
        if len(stock_positions) <= 0:
            logger.error("failed to get current position")
            exit(1)
        return stock_positions

    def __getCleanedData(self, cols = 16):
        self.restoreWindow()
        self.__init__()
        self.__dialog_window.CVirtualGridCtrl.right_click(coords=(30, 30))
        self.__main_window.type_keys('C')
        time.sleep(self.sleep_time)
        popup_window = self.__main_window.popup_window()
        if popup_window:
            popup_window = self.__app.window(handle=popup_window)
            popup_window.capture_as_image().save("v_code.png")
            vcode = get_vcode('v_code.png')
            popup_window.set_focus()
            popup_window.Edit.set_focus()
            time.sleep(self.sleep_time)
            popup_window.Edit.set_edit_text(vcode)
            time.sleep(self.sleep_time)
            popup_window.child_window(title=u"确定", class_name="Button").Click()

        data = pywinauto.clipboard.GetData()  # Copy from clipboard directly after manual copy
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
            self.__closePopupWindows()

            price = "%.2f" % price
            if direction == 'B':
                self.__buy(code, price, quantity)
            if direction == 'S':
                self.__sell(code, price, quantity)
            self.__closePopupWindows()
            # self.minWindow()
            self.saveScreenshot("Ordered: [%s - %s - %.2f - %d]" % (code, direction, float(price), quantity),
                                u'操作：%s' % direction)
            return True
        except Exception as exc:
            logger.error("Failed to order: %s" % exc)
            return False

    def maxWindow(self):
        logger.info("maximize current window")
        if self.__main_window.get_show_state() != 3:
            self.__main_window.Maximize()
        self.__main_window.set_focus()
        time.sleep(self.sleep_time)

    def minWindow(self):
        logger.info("minimize current window")
        if self.__main_window.get_show_state() != 2:
            self.__main_window.Minimize()

    def restoreWindow(self):
        if self.__main_window.has_style(win32defines.WS_MINIMIZE): # if minimized
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
            keyboard.send_keys("{F4}")
            time.sleep(2*self.sleep_time)
            keyboard.send_keys("{F5}")
            time.sleep(2*self.sleep_time)
            keyboard.send_keys("{F5}")
            time.sleep(2*self.sleep_time)
            self.__main_window.capture_as_image().save(picName)
            time.sleep(self.sleep_time)
            self.screenshotCount += 1
            sendEmail([picName], status, title)
        except Exception as e:
            logger.error("Failed to send email: %s" % e)


if __name__ == '__main__':
    tong_hua_shun = OperationOfThs()
    tong_hua_shun.start()

    tong_hua_shun.order('600570', 'B', 0, 200)
    tong_hua_shun.order('600570', 'S', 0, 200)

    chen_ben = tong_hua_shun.getChenben()
    logger.info("chen ben: %s" % chen_ben)

    position = tong_hua_shun.getPosition()
    logger.info("position: %s" % position)

    tong_hua_shun.stop()
