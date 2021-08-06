#!/bin/env python
# -*- coding: utf-8 -*-
import time
import traceback
import ths_window
import time_util
import bs_direction_compose as direct_cli
from deal_entries import DealEntries
from ths_cli import ThsCli
from logger_util import logger


class AutoDeal:
    def __init__(self):
        self.start_ths()
        self.ths_cli = ThsCli()
        self.deal_entries = DealEntries(self.ths_cli.get_cost(), self.ths_cli.get_volume())
        self.ths_cli.save_screenshot("initial done for %d codes" % len(self.deal_entries.codes), "initial done")

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
        sleep_count = 0
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
                sleep_count = sleep_count + 30
                if sleep_count % 1800 == 0:
                    self.ths_cli.save_screenshot("status update", "status update")
            except Exception as exe:
                logger.error("exception during deal loop: %s" % exe)
                track = traceback.format_exc()
                print(track)
                time.sleep(30)


def is_within_deal_window():
    if time_util.compare_time("09", "26") and not time_util.compare_time("15", "00"):
        return True
    return False


if __name__ == "__main__":
    while True:
        try:
            week_day = time.localtime().tm_wday
            if week_day >= 5:
                logger.info("now is Saturday, sleep to wait for deal time")
                time.sleep(3600)
                continue

            if not is_within_deal_window():
                logger.info("not deal window, sleep to wait for deal time")
                time.sleep(60)
                continue

            logger.info("time to start auto deal")
            time.sleep(60)
            auto_deal = AutoDeal()
            auto_deal.test()
            auto_deal.loop()
            logger.info("out of deal time now")
            direct_cli.update_cache()
            direct_cli.update_candidates()
        except Exception as exe:
            logger.error("exception during main loop, %s" % exe)
            track = traceback.format_exc()
            print(track)
            time.sleep(60)
