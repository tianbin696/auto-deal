#!/bin/env python
# -*- coding: utf-8 -*-
import bs_direction_avg as avg
import bs_direction_rsi as rsi
import ts_cli as ts
from logger_util import logger


def get_direction(prices):
    __direction = avg.get_direction(prices)
    if __direction == "B" or __direction == "S":
        logger.info("direction based on average: %s" % __direction)
        return __direction

    __direction = rsi.get_direction(prices)
    if __direction == "B" or __direction == "S":
        logger.info("direction based on RSI: %s" % __direction)
    return __direction


if __name__ == "__main__":
    df = ts.get_h_data("601100.SH", start_date="20200730", end_date="20210730")
    for i in range(0, 120):
        updated_prices = []
        updated_prices.extend(df['close'][i:])
        direction = get_direction(updated_prices)
        if direction == "B" or direction == "S":
            print "direction of %s: %s - %.2f" % (df['trade_date'][i], direction, df['close'][i])
