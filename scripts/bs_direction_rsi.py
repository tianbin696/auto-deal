#!/bin/env python
# -*- coding: utf-8 -*-
import ts_cli as ts


def get_direction(prices):
    rsi_01 = get_rsi(prices, 6)
    rsi_02 = get_rsi(prices, 12)
    rsi_03 = get_rsi(prices, 24)
    rsi_11 = get_rsi(prices[1:], 6)
    rsi_12 = get_rsi(prices[1:], 12)
    rsi_13 = get_rsi(prices[1:], 24)
    if rsi_11 < rsi_12 < rsi_13:
        if rsi_01 > rsi_02:
            return "B"
    if rsi_11 > rsi_12 > rsi_13:
        if rsi_01 < rsi_02:
            return "S"
    return "N"


def get_rsi(prices, days=14):
    positive_sum = 0
    positive_count = 0
    negative_sum = 0
    negative_count = 0
    for i in range(0, days):
        increase = (prices[i] - prices[i+1])/prices[i+1]
        if increase > 0:
            positive_sum += increase
            positive_count += 1
        else:
            negative_sum += increase
            negative_count += 1
    result = (positive_sum*100) / (positive_sum + abs(negative_sum))
    return int(result)


if __name__ == "__main__":
    df = ts.get_h_data("601100.SH", start_date="20200730", end_date="20210730")

    rsi_value = get_rsi(df['close'], days=6)
    print "RSI-6 value: %d" % rsi_value

    rsi_value = get_rsi(df['close'], days=12)
    print "RSI-12 value: %d" % rsi_value

    rsi_value = get_rsi(df['close'], days=24)
    print "RSI-24 value: %d" % rsi_value

    for i in range(0, 120):
        updated_prices = []
        updated_prices.extend(df['close'][i:])
        direction = get_direction(updated_prices)
        if direction == "B" or direction == "S":
            print "direction of %s: %s - %.2f" % (df['trade_date'][i], direction, df['close'][i])

