#!/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import ts_cli as ts


def get_direction(df):
    __df = __get_macd(df, 12, 26, 9)
    if __df['macd'][0] > 0 > __df['macd'][1]:
        return 'B'
    if __df['macd'][0] < 0 < __df['macd'][1]:
        return 'S'
    return 'N'


def __get_ema(df, N):
    for i in range(len(df)-1, -1, -1):
        if i == len(df)-1:
            df.ix[i, 'ema'] = df.ix[i, 'close']
        if i < len(df)-1:
            df.ix[i, 'ema'] = (2*df.ix[i, 'close']+(N-1)*df.ix[i+1, 'ema'])/(N+1)
    __ema = list(df['ema'])
    return __ema


def __get_macd(df, short=12, long=26, M=9):
    a = __get_ema(df, short)
    b = __get_ema(df, long)
    df['diff'] = pd.Series(a)-pd.Series(b)
    for i in range(len(df)-1, -1, -1):
        if i == len(df)-1:
            df.ix[i, 'dea'] = df.ix[i, 'diff']
        if i < len(df)-1:
            df.ix[i, 'dea'] = (2*df.ix[i, 'diff']+(M-1)*df.ix[i+1, 'dea'])/(M+1)
    df['macd'] = 2*(df['diff']-df['dea'])
    return df


if __name__ == "__main__":
    df = ts.get_h_data("600570.SH", start_date="20200730", end_date="20210730")
    df = __get_macd(df, 12, 26, 9)
    print df[0:30]

    for i in range(0, 120):
        d = {'close': df['close'][i:]}
        __df = pd.DataFrame(d).reset_index()
        direction = get_direction(__df)
        if direction == "B" or direction == "S":
            print "direction of %s: %s - %.2f" % (df['trade_date'][i], direction, df['close'][i])
