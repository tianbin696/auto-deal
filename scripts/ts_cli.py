#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os

import pandas
import tushare as ts

import scripts.file_locator as locator

token = "3f249c0d4e9d93e62dd5a5b2c96dd75272e715fbfe8e972bf786aa9f"
ts.set_token(token)


def get_h_data(code='600570.SH', start_date='20200101', end_date='20210101'):
    __df = ts.pro_bar(ts_code=code, adj="qfq", start_date=start_date, end_date=end_date)
    return __df


def get_rt_price(code):
    __df = ts.get_realtime_quotes(code)
    return __df


def get_h_data_cache(code='600570.SH', start_date='20200101', end_date='20210101', force_update=False):
    cache_folder = locator.get_path("cache")
    cache_file = cache_folder + "/" + code + ".csv"
    if not os.path.exists(cache_folder):
        os.mkdir(cache_folder)

    if os.path.exists(cache_file) and not force_update:
        __df = pandas.read_csv(cache_file)
    else:
        __df = ts.pro_bar(ts_code=code, adj="qfq", start_date=start_date, end_date=end_date)
        if len(__df) > 0:
            writer = open(cache_file, "w")
            __df.to_csv(writer)
            writer.close()
        __df = pandas.read_csv(cache_file)
    return __df


def update_cache():
    for __code in list(open("code_hs_300.txt")):
        __code = __code.strip()
        if __code.startswith('0') or __code.startswith('3'):
            __code = "%s.SZ" % __code
        else:
            __code = "%s.SH" % __code
        end_date = (datetime.datetime.now()).strftime("%Y%m%d")
        get_h_data_cache(__code, "20100101", end_date, True)
        print("cached %s" % __code)


if __name__ == "__main__":
    df = get_h_data("600570.SH")
    print(df[0:3])

    end_date_str = (datetime.datetime.now()).strftime("%Y%m%d")
    df = get_h_data("600570.SH", end_date=end_date_str)
    print(df[0:3])

    df = get_rt_price("600570")
    print(df)

    update_cache()
