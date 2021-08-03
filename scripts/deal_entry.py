#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import time_util
import bs_direction_compose as direct_cli
import bs_price
import bs_volume
import ts_cli as ts
from logger_util import logger


class DealEntry:
    def __init__(self, code, cost, volume):
        self.code = code
        self.cost = cost
        self.volume = volume
        self.is_intra_day = True
        self.is_buyed = False
        self.is_selled = False
        self.buy_vol = 0
        self.yesterday_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        self.h_code = "%s.SH" % code
        if code < "600000":
            self.h_code = "%s.SZ" % code
        self.h_data = ts.get_h_data(self.h_code, end_date=self.yesterday_str)
        logger.info("initialized")
        logger.info("code=%s, h_code=%s, cost=%.2f, volume=%d, yesterday=%s" % (self.code, self.h_code, self.cost,
                                                                                self.volume, self.yesterday_str))
        logger.info("historical data: %s" % self.h_data[0:3])

    def get_rt_deal(self):
        if self.is_buyed and self.is_selled:
            return None
        rt_df = ts.get_rt_price(self.code)
        rt_price = float(rt_df['price'][0])

        if self.is_intra_day and self.is_buyed and not self.is_selled:
            if is_closing_deal_window() or rt_price > float(rt_df['pre_close'][0])*1.09:
                __volume = self.buy_vol
                __price = bs_price.get_sell_price(rt_price)
                self.is_selled = True
                return [self.code, "S", __price, __volume]

        __direction = direct_cli.get_direction(rt_df, self.h_data, self.is_intra_day)
        logger.info("realtime direction for code %s: %s" % (self.code, __direction))

        if __direction == "B" and not self.is_buyed:
            __volume = bs_volume.get_buy_vol(rt_price)
            __price = bs_price.get_buy_price(rt_price)
            self.is_buyed = True
            if self.is_intra_day:
                self.buy_vol = __volume
            return [self.code, "B", __price, __volume]
        if __direction == "S" and not self.is_selled:
            __volume = bs_volume.get_sell_vol(self.volume, rt_price)
            __price = bs_price.get_sell_price(rt_price)
            self.is_selled = True
            return [self.code, "S", __price, __volume]
        return None


def is_closing_deal_window():
    if time_util.compare_time("14", "50"):
        return True
    return False


if __name__ == "__main__":
    deal_main = DealEntry("600570", 55.01, 200)
    deal_main.is_buyed = True
    deal = deal_main.get_rt_deal()
    if deal:
        print deal
    else:
        print "No deal expected"
