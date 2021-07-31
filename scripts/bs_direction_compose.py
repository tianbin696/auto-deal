#!/bin/env python
# -*- coding: utf-8 -*-
import logging
import ts_cli as ts
import pandas as pd
import bs_direction_avg as avg
import bs_direction_rsi as rsi
import bs_direction_macd as macd


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../../logs/auto_deal_ths.log',
                    filemode='a')
logger = logging.getLogger('bs_direction_compose')


def get_direction(prices):
    __direction = avg.get_direction(prices)
    if __direction == "B" or __direction == "S":
        logger.info("direction based on average: %s" % __direction)
        return __direction

    # d = {'close': prices[0:52]}
    # __df = pd.DataFrame(d).reset_index()
    # __direction = macd.get_direction(__df)
    # if __direction == "B" or __direction == "S":
    #     return __direction

    __direction = rsi.get_direction(prices)
    if __direction == "B" or __direction == "S":
        logger.info("direction based on RSI: %s" % __direction)
    return __direction


if __name__ == "__main__":
    df = ts.get_h_data("600570.SH", start_date="20200730", end_date="20210730")

    for i in range(0, 120):
        updated_prices = []
        updated_prices.extend(df['close'][i:])
        direction = get_direction(updated_prices)
        if direction == "B" or direction == "S":
            print "direction of %s: %s - %.2f" % (df['trade_date'][i], direction, df['close'][i])
