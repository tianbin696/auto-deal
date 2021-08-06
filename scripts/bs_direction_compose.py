#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import bs_direction_avg as avg
import bs_direction_rsi as rsi
import bs_direction_intra_day as intra
import ts_cli as ts
import pandas as pd
from logger_util import logger


def get_direction(rt_df_in, df_h_in, is_intra_day_deal):
    rt_price = float(rt_df_in['price'][0])
    if rt_price <= 0:
        return "N"

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


def update_cache():
    ts.update_cache()


def update_candidates():
    code_list = intra.get_candidates()
    if len(code_list) > 0:
        writer = open("code_candidates.txt", 'w')
        writer.write(code_list[0])
        for __code in code_list[1:]:
            writer.write("\n" + __code)
        writer.close()
    return code_list


if __name__ == "__main__":
    # codes = update_candidates()
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
    deal_codes = []
    for code in list(open("code_candidates.txt")):
        code = code.strip()
        if code.startswith("6"):
            code = "%s.SH" % code
        else:
            code = "%s.SZ" % code
        df_h = ts.get_h_data_cache(code, start_date="20160101", end_date=end_date)
        df_h_in = df_h[1:].reset_index()

        d = {'price': [df_h['high'][0]-0.01], 'open': [df_h['open'][0]], 'high': [df_h['high'][0]], 'low': [df_h['low'][0]],
             'volume': [df_h['vol'][0]], 'pre_close': [df_h['close'][1]]}
        df_rt = pd.DataFrame(d).reset_index()
        direction = get_direction(df_rt, df_h_in, True)
        if direction == "B" or direction == "S":
            print "%s, direction: %s - %.2f" % (code, direction, df_rt['price'][0])
            deal_codes.append("%s-%s" % (code, direction))
            continue

        d = {'price': [df_h['open'][0]+0.01], 'open': [df_h['open'][0]], 'high': [df_h['high'][0]], 'low': [df_h['low'][0]],
             'volume': [df_h['vol'][0]], 'pre_close': [df_h['close'][1]]}
        df_rt = pd.DataFrame(d).reset_index()
        direction = get_direction(df_rt, df_h_in, True)
        if direction == "B" or direction == "S":
            print "%s, direction: %s - %.2f" % (code, direction, df_rt['price'][0])
            deal_codes.append("%s-%s" % (code, direction))
            continue

        d = {'price': [df_h['close'][0]], 'open': [df_h['open'][0]], 'high': [df_h['high'][0]], 'low': [df_h['low'][0]],
             'volume': [df_h['vol'][0]], 'pre_close': [df_h['close'][1]]}
        df_rt = pd.DataFrame(d).reset_index()
        direction = get_direction(df_rt, df_h_in, True)
        if direction == "B" or direction == "S":
            print "%s, direction: %s - %.2f" % (code, direction, df_rt['price'][0])
            deal_codes.append("%s-%s" % (code, direction))
            continue

        d = {'price': [df_h['low'][0]+0.01], 'open': [df_h['open'][0]], 'high': [df_h['high'][0]], 'low': [df_h['low'][0]],
             'volume': [df_h['vol'][0]], 'pre_close': [df_h['close'][1]]}
        df_rt = pd.DataFrame(d).reset_index()
        direction = get_direction(df_rt, df_h_in, True)
        if direction == "B" or direction == "S":
            print "%s, direction: %s - %.2f" % (code, direction, df_rt['price'][0])
            deal_codes.append("%s-%s" % (code, direction))
            continue

    print deal_codes
