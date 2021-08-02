#!/bin/env python
# -*- coding: utf-8 -*-
import bs_direction_avg as avg
import bs_direction_rsi as rsi
import bs_direction_intra_day as intra
import ts_cli as ts
import pandas as pd
from logger_util import logger


def get_direction(rt_df_in, df_h_in, is_intra_day_deal):
    rt_price = float(rt_df_in['price'][0])
    if is_intra_day_deal:
        __direction = intra.get_direction(rt_df_in, df_h_in)
        logger.info("direction based on intra: %s" % __direction)
        return __direction

    prices = [rt_price]
    prices.extend(df_h_in['close'])
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
        d = {'price': df['high'][i:i+1], 'open': df['open'][i:i+1], 'high': df['high'][i:i+1], 'low': df['low'][i:i+1],
             'volume': df['vol'][i:i+1]}
        __rt_df = pd.DataFrame(d).reset_index()
        direction = get_direction(__rt_df, df[i+1:].reset_index(), True)
        if direction == "B" or direction == "S":
            print "direction of %s: %s - %.2f" % (df['trade_date'][i], direction, df['close'][i])
