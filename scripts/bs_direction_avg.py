#!/bin/env python
# -*- coding: utf-8 -*-
import ts_cli as ts
import numpy


def get_direction(prices):
    avg_01 = numpy.mean(prices[0:5])
    avg_02 = numpy.mean(prices[0:10])
    avg_03 = numpy.mean(prices[0:30])

    avg_11 = numpy.mean(prices[1:6])
    avg_12 = numpy.mean(prices[1:11])
    avg_13 = numpy.mean(prices[1:31])

    if avg_12 > avg_11 > avg_13:
        if avg_01 > avg_02 > avg_03:
            return "B"
    if avg_11 > avg_12 > avg_13:
        if avg_02 > avg_01 > avg_03:
            return "S"
    return "N"


if __name__ == "__main__":
    df = ts.get_h_data("600570.SH", start_date="20200730", end_date="20210730")

    for i in range(0, 120):
        updated_prices = []
        updated_prices.extend(df['close'][i:])
        direction = get_direction(updated_prices)
        if direction == "B" or direction == "S":
            print "direction of %s: %s - %.2f" % (df['trade_date'][i], direction, df['close'][i])
