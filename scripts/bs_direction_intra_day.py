#!/bin/env python
# -*- coding: utf-8 -*-
import numpy
import ts_cli as ts


def get_direction(price_in, df_h_in, days_in=10):
    upper_line = numpy.max(df_h_in['high'][0:days_in])
    if numpy.mean(df_h_in['close'][0:5]) < price_in < numpy.mean(df_h_in['close'][0:5])*1.20:
        if price_in > upper_line:
            return "B"
    return "N"


if __name__ == "__main__":
    for code in ['002032.SZ', '002311.SZ', '002271.SZ', '600161.SH', '601100.SH', '603899.SH']:
        df = ts.get_h_data(code, start_date="20150730", end_date="20210730")
        count = 0
        total_profit = 0
        days = 10
        for i in range(1, 300):
            __df = df[i+1:].reset_index()
            direction = get_direction(df['high'][i], __df, days)
            if direction == "B":
                count = count + 1
                profit = (df['close'][i]-numpy.max(df['high'][i+1:i+1+days]))*100/numpy.max(df['high'][i+1:i+1+days])
                total_profit = total_profit + profit
                print "profit of %s: %s, %%%.2f" % (df['trade_date'][i], direction, profit)
        print "code: %s, count: %d, average profit: %%%.2f" % (code, count, total_profit/count)
