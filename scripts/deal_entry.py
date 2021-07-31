#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
import bs_direction_compose as direct_cli
import bs_price
import bs_volume
import ts_cli as ts

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../../logs/auto_deal_ths.log',
                    filemode='a')
logger = logging.getLogger('deal_entry')


class DealEntry:
    def __init__(self, code, cost, volume):
        self.code = code
        self.cost = cost
        self.volume = volume
        self.is_dealed = False
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
        if self.is_dealed:
            return None
        rt_df = ts.get_rt_price(self.code)
        rt_price = float(rt_df['price'][0])
        updated_prices = [rt_price]
        updated_prices.extend(self.h_data['close'])
        logger.info("prices for code %s: %s" % (self.code, updated_prices[0:5]))
        __direction = direct_cli.get_direction(updated_prices)
        logger.info("realtime direction for code %s: %s" % (self.code, __direction))

        if __direction == "B":
            __volume = bs_volume.get_buy_vol(rt_price)
            __price = bs_price.get_buy_price(rt_price)
            self.is_dealed = True
            return [self.code, "B", __price, __volume]
        if __direction == "S":
            __volume = bs_volume.get_sell_vol(self.volume)
            __price = bs_price.get_sell_price(rt_price)
            self.is_dealed = True
            return [self.code, "S", __price, __volume]
        return None


if __name__ == "__main__":
    deal_main = DealEntry("600570", 55.01, 200)
    deal = deal_main.get_rt_deal()
    if deal:
        print deal
    else:
        print "No deal expected"
