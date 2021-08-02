#!/bin/env python
# -*- coding: utf-8 -*-
import numpy
import pandas as pd

import ts_cli as ts


def get_direction(rt_df_in, df_h_in, days_in=20):
    price_in = rt_df_in['price'][0]
    open_price = rt_df_in['open'][0]
    upper_line = numpy.max(df_h_in['high'][0:days_in])
    if numpy.mean(df_h_in['close'][0:5]) < price_in < numpy.mean(df_h_in['close'][0:5])*1.20:
        if price_in > upper_line and price_in > open_price:
            return "B"
    return "N"


if __name__ == "__main__":
    final_list = []
    for code in list(open("../codes/hs_300.txt")):
        try:
            code = code.strip()
            if code.startswith('0') or code.startswith('3'):
                code = "%s.SZ" % code
            else:
                code = "%s.SH" % code
            df = ts.get_h_data(code, start_date="20150730", end_date="20210730")
            count = 0
            total_profit = 0
            days = 20
            for i in range(1, 500):
                d = {'price': df['high'][i:i+1], 'open': df['open'][i:i+1], 'high': df['high'][i:i+1], 'low': df['low'][i:i+1],
                     'volume': df['vol'][i:i+1]}
                __rt_df = pd.DataFrame(d).reset_index()
                __df = df[i+1:].reset_index()
                direction = get_direction(__rt_df, __df, days)
                if direction == "B":
                    count = count + 1
                    profit = (df['close'][i]-numpy.max(df['high'][i+1:i+1+days]))*100/numpy.max(df['high'][i+1:i+1+days])
                    total_profit = total_profit + profit
                    print "profit of %s: %s, %%%.2f" % (df['trade_date'][i], direction, profit)
            avg_profit = total_profit/count
            if avg_profit > 0.6 and count > 50:
                final_list.append(code)
            print "code: %s, count: %d, average profit: %%%.2f" % (code, count, avg_profit)
        except Exception as exe:
            print "error for code %s" % code
    print "final list: %s" % final_list
