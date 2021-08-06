#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import numpy
import pandas as pd
import ts_cli as ts


def get_direction(rt_df_in, df_h_in, days_in=20):
    __direction = get_direction_phiary(rt_df_in, df_h_in, days_in)[0]
    if __direction != "N":
        return __direction
    return "N"


def get_direction_phiary(rt_df_in, df_h_in, days_in=20):
    # 菲阿里四价模型
    price_in = float(rt_df_in['price'][0])
    open_price = float(rt_df_in['open'][0])
    high_price = float(rt_df_in['high'][0])
    pre_close = float(rt_df_in['pre_close'][0])
    upper_line = numpy.max(df_h_in['high'][0:days_in])
    lower_line = numpy.min(df_h_in['low'][0:days_in])
    if float(rt_df_in['price'][0]) <= 0:
        # For testing
        price_in = min(max(open_price, numpy.max(df_h_in['high'][0:days_in]))+0.01, high_price)
    if max(upper_line, open_price) < price_in < pre_close*1.06:
        # For testing
        buy_price = max(open_price, numpy.max(df_h_in['high'][0:days_in]))
        return ["B", buy_price]
    if price_in < lower_line and price_in < open_price:
        return ["S"]
    return ["N"]


def get_candidates(codes=None):
    final_list = []
    if not codes:
        codes = list(open("code_hs_300.txt"))
    for __code in codes:
        try:
            code_new = __code.strip()
            if code_new.startswith('0') or code_new.startswith('3'):
                code_new = "%s.SZ" % code_new
            else:
                code_new = "%s.SH" % code_new
            end_date = (datetime.datetime.now()).strftime("%Y%m%d")
            df = ts.get_h_data_cache(code_new, start_date="20160101", end_date=end_date)
            count = 0
            total_profit = 0
            days = 20
            for i in range(1, 300):
                d = {'price': [0], 'open': [df['open'][i]], 'high': [df['high'][i]], 'low': [df['low'][i]],
                     'volume': [df['vol'][i]], 'pre_close': [df['close'][i+1]]}
                __rt_df = pd.DataFrame(d).reset_index()
                __df = df[i+1:].reset_index()
                __resp = get_direction_phiary(__rt_df, __df, days)
                __direction = __resp[0]
                if __direction == "B":
                    count = count + 1
                    buy_price = __resp[1]
                    profit = (df['close'][i]-buy_price)*100/buy_price
                    total_profit = total_profit + profit
                    print "profit of %s: %s, %%%.2f" % (df['trade_date'][i], __direction, profit)
            avg_profit = total_profit/count
            if avg_profit > 0.5 and count > 30 and df['close'][0] < 200:
                final_list.append(__code.strip())
            print "code: %s, count: %d, average profit: %%%.2f" % (code_new, count, avg_profit)
            print "final list: %s" % final_list
        except Exception as exe:
            print "error for code %s" % __code
    return final_list


def test_buy(code, start_date, end_date):
    df = ts.get_h_data(code, start_date=start_date, end_date=end_date)
    d = {'price': [max(df['low'][0], min(numpy.max(df['high'][0:20])+0.01, df['high'][0]))], 'open': [df['open'][0]],
         'high': [df['high'][0]], 'low': [df['low'][0]], 'volume': [df['vol'][0]], 'pre_close': [df['close'][1]]}
    __rt_df = pd.DataFrame(d).reset_index()
    __df = df[1:].reset_index()
    __direction = get_direction(__rt_df, __df)
    return __direction


def test_sell(code, start_date, end_date):
    df = ts.get_h_data(code, start_date=start_date, end_date=end_date)
    d = {'price': [df['low'][0]], 'open': [df['open'][0]], 'high': [df['high'][0]], 'low': [df['low'][0]],
         'volume': [df['vol'][0]], 'pre_close': [df['close'][1]]}
    __rt_df = pd.DataFrame(d).reset_index()
    __df = df[1:].reset_index()
    __direction = get_direction(__rt_df, __df)
    return __direction


if __name__ == "__main__":
    direction = test_buy("601100.SH", "20160101", "20210803")
    assert direction == "B"

    direction = test_buy("601100.SH", "20160101", "20210802")
    assert direction == "N"

    direction = test_buy("601100.SH", "20160101", "20210728")
    assert direction == "N"

    direction = test_sell("601100.SH", "20160101", "20210222")
    assert direction == "S"

    code_list = get_candidates()
    if len(code_list) > 0:
        writer = open("code_candidates.txt", 'w')
        writer.write(code_list[0])
        for __code in code_list[1:]:
            writer.write("\n" + __code)
        writer.close()
