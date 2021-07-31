#!/bin/env python
# -*- coding: utf-8 -*-
import logging
import time
import ths_window
import time_util
from deal_entries import DealEntries
from ths_cli import ThsCli

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
console.setFormatter(formatter)
logger = logging.getLogger('deal_starter')
logger.addHandler(console)


class AutoDeal:
    def __init__(self):
        self.start_ths()
        self.ths_cli = ThsCli()
        self.deal_entries = DealEntries(self.ths_cli.get_cost(), self.ths_cli.get_volume())

    def start_ths(self):
        ths_window.ths_start()
        logger.info("THS window opened")

    def close_ths(self):
        self.ths_cli.save_screenshot("Closing THS", "Closing THS")
        ths_window.ths_close()
        logger.info("THS window closed")

    def test(self):
        logger.info("testing before deal start")
        self.ths_cli.order('600570', 'B', 0, 200)
        self.ths_cli.order('600570', 'S', 0, 200)
        logger.info("testing finished")

    def loop(self):
        while True:
            try:
                self.ths_cli.move_mouse()
                if not is_within_deal_window():
                    logger.info("not deal window, exit")
                    self.close_ths()
                    break
                __deals = self.deal_entries.get_deals()
                for deal in __deals:
                    self.ths_cli.order(deal[0], deal[1], deal[2], deal[3])
                time.sleep(30)
            except Exception as exe:
                logger.error("exception during deal loop: %s" % exe)


def is_within_deal_window():
    if time_util.compare_time("09", "25") and not time_util.compare_time("15", "05"):
        return True
    return False


if __name__ == "__main__":
    while True:
        try:
            week_day = time.localtime().tm_wday
            if week_day == 5:
                logger.info("now is Saturday, sleep to wait for deal time")
                time.sleep(3600)
                continue

            if not is_within_deal_window():
                logger.info("not deal window, sleep to wait for deal time")
                time.sleep(60)
                continue

            logger.info("time to start auto deal")
            auto_deal = AutoDeal()
            auto_deal.loop()
            logger.info("out of deal time now")
        except Exception as exe:
            logger.error("exception during loop, %s" % exe)
