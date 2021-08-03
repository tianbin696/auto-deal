#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import tushare as ts

token = "3f249c0d4e9d93e62dd5a5b2c96dd75272e715fbfe8e972bf786aa9f"
ts.set_token(token)


def get_h_data(code='600570.SH', start_date='20200101', end_date='20210101'):
    __df = ts.pro_bar(ts_code=code, adj="qfq", start_date=start_date, end_date=end_date)
    return __df


def get_rt_price(code):
    __df = ts.get_realtime_quotes(code)
    return __df


if __name__ == "__main__":
    df = get_h_data("600570.SH")
    print df[0:3]

    end_date_str = (datetime.datetime.now()).strftime("%Y%m%d")
    df = get_h_data("600570.SH", end_date=end_date_str)
    print df[0:3]

    df = get_rt_price("600570")
    print df
