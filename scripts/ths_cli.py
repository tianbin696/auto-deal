#!/bin/env python
# -*- coding: utf-8 -*-
import logging
import random
import time
from datetime import datetime
import pywinauto
import pywinauto.application
import pywinauto.clipboard
from pywinauto import keyboard
from pywinauto import mouse
from pywinauto import win32defines
from pywinauto.win32functions import SetForegroundWindow, ShowWindow
from email_cli import send_email
from ths_window import ths_start, ths_close
# from vcode_cli import get_vcode

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
console.setFormatter(formatter)
logger = logging.getLogger('ths_cli')
logger.addHandler(console)


class ThsCli:
    def __init__(self):
        self.sleep_time = 0.5
        self.screenshotCount = 1
        self.__app = pywinauto.application.Application()
        try:
            logger.info("connecting THS ...")
            self.__app.connect(title=u'网上股票交易系统5.0')
            logger.info("connected THS")
            top_window = pywinauto.findwindows.find_window(title=u'网上股票交易系统5.0')
            self.__main_window = self.__app.window(handle=top_window)
            self.__dialog_window = self.__app.window(handle=top_window)
        except Exception as e:
            logger.info("error during init THS: %s" % e)
            exit(1)

    def __buy(self, code, price, quantity):
        keyboard.send_keys("{F1}")
        time.sleep(self.sleep_time)

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

        self.__dialog_window[u'卖出Button'].click()
        # self.__dialog_window.child_window(title=u"卖出", class_name="Button").Click()
        time.sleep(self.sleep_time)

    def __close_popup_windows(self):
        logger.info("closing popup windows")
        time.sleep(4 * self.sleep_time)  # wait for popup window to appear
        while self.__close_popup_window():
            time.sleep(4 * self.sleep_time)

    def __close_popup_window(self):
        logger.info("closing popup window")
        popup_window = self.__main_window.popup_window()
        if popup_window:
            try:
                popup_window = self.__app.window(handle=popup_window)
                popup_window.set_focus()
                popup_window.Button.click()
            except Exception as e:
                logger.warn("cannot close popup window %s, trying force close" % e)
                keyboard.send_keys('%{F4}')
            return True
        return False

    def get_cost(self):
        data = self.__get_cleaned_data()
        stock_costs = {}
        for index in range(1, len(data)):
            # code = position[index][1].encode() # for VM
            code = data[index][1]
            cost = data[index][6]
            stock_costs[code] = float(cost)

        logger.info("costs: %s" % stock_costs)
        if len(stock_costs) <= 0:
            logger.error("failed to get current costs")
            exit(1)
        return stock_costs

    def get_volume(self):
        data = self.__get_cleaned_data()
        stock_volumes = {}
        for index in range(1, len(data)):
            # code = position[index][1].encode() # for VM
            code = data[index][1]
            volume = data[index][3]
            # if position[index][3] != position[index][4]:
            #     amount = 0
            stock_volumes[code] = int(volume)

        logger.info("volumes: %s" % stock_volumes)
        if len(stock_volumes) <= 0:
            logger.error("failed to get current volumes")
            exit(1)
        return stock_volumes

    def __get_cleaned_data(self):
        self.restore_window()
        self.__dialog_window.CVirtualGridCtrl.right_click(coords=(30, 30))
        self.__main_window.type_keys('C')
        time.sleep(self.sleep_time)
        # Logic to handle case that need v_code to copy values
        # popup_window = self.__main_window.popup_window()
        # if popup_window:
        #     popup_window = self.__app.window(handle=popup_window)
        #     popup_window.capture_as_image().save("v_code.png")
        #     vcode = get_vcode('v_code.png')
        #     popup_window.set_focus()
        #     popup_window.Edit.set_focus()
        #     time.sleep(self.sleep_time)
        #     popup_window.Edit.set_edit_text(vcode)
        #     time.sleep(self.sleep_time)
        #     popup_window.child_window(title=u"确定", class_name="Button").Click()

        data = pywinauto.clipboard.GetData()  # Copy from clipboard directly after manual copy
        lst = data.strip().split("\r\n")
        matrix = []
        for i in range(0, len(lst)):
            sub_list = lst[i].split("\t")
            matrix.append(sub_list)

        return matrix

    def order(self, code, direction, price, quantity):
        logger.info("trying to order: [%s - %s - %.2f - %d]" % (code, direction, price, quantity))
        try:
            self.restore_window()

            price = "%.2f" % price
            if direction == 'B':
                self.__buy(code, price, quantity)
            if direction == 'S':
                self.__sell(code, price, quantity)
            self.__close_popup_window()
            self.save_screenshot("ordered: [%s - %s - %.2f - %d]" % (code, direction, float(price), quantity),
                                u'操作：%s' % direction)
            return True
        except Exception as exc:
            logger.error("failed to order: %s" % exc)
            return False

    def restore_window(self):
        if self.__main_window.has_style(win32defines.WS_MINIMIZE):  # if minimized
            ShowWindow(self.__main_window.wrapper_object(), 9)  # restore window state
        else:
            SetForegroundWindow(self.__main_window.wrapper_object())  # bring to front

    def save_screenshot(self, status, title):
        try:
            self.__close_popup_windows()
            pic_name = "../../logs/auto_deal_%s.png" % datetime.now().strftime("%Y-%m-%d_%H-%M")
            self.restore_window()
            keyboard.send_keys("{F4}")
            time.sleep(2*self.sleep_time)
            keyboard.send_keys("{F5}")
            time.sleep(2*self.sleep_time)
            keyboard.send_keys("{F5}")
            time.sleep(2*self.sleep_time)
            self.__main_window.capture_as_image().save(pic_name)
            time.sleep(self.sleep_time)
            self.screenshotCount += 1
            send_email([pic_name], status, title)
        except Exception as e:
            logger.error("failed to send email: %s" % e)

    def move_mouse(self):
        # move mouse randomly to prevent screen locked
        mouse.move(coords=(random.randint(0, 99), random.randint(0, 99)))


if __name__ == '__main__':
    ths_start()

    tong_hua_shun = ThsCli()

    tong_hua_shun.order('600570', 'B', 0, 200)
    tong_hua_shun.order('600570', 'S', 0, 200)

    chen_ben = tong_hua_shun.get_cost()
    position = tong_hua_shun.get_volume()

    ths_close()
