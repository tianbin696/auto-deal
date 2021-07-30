#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging

import ts_cli as ts

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../../logs/auto_deal_ths.log',
                    filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
console.setFormatter(formatter)
logger = logging.getLogger('deal_main')
logger.addHandler(console)


class DealMain:
    def __init__(self, code, cost, volume):
        self.code = code
        self.cost = cost
        self.volume = volume
        self.yesterday_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        self.h_code = "%s.SH" % code
        if code < "600000":
            self.h_code = "%s.SZ" % code
        self.h_data = ts.get_h_data(self.h_code, end_date=self.yesterday_str)
        logger.info("initialized")
        logger.info("code=%s, h_code=%s, cost=%.2f, volume=%d, yesterday=%s" % (self.code, self.h_code, self.cost,
                                                                                self.volume, self.yesterday_str))
        logger.info("historical data: %s" % self.h_data[0:3])


if __name__ == "__main__":
    deal_main = DealMain("600570", 55.01, 200)
