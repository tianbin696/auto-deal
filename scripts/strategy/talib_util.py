#!/bin/env python
import talib as ta
import numpy as np


def SMA_CN(close, timeperiod):
    return reduce(lambda x, y: ((timeperiod - 1) * x + y) / timeperiod, close)


def RSI_CN(close, timeperiod):
    close = close[::-1]
    diff = map(lambda x, y: x - y, close[1:], close[:-1])
    diffGt0 = map(lambda x: 0 if x < 0 else x, diff)
    diffABS = map(lambda x: abs(x), diff)
    diff = np.array(diff)
    diffGt0 = np.array(diffGt0)
    diffABS = np.array(diffABS)
    diff = np.append(diff[0], diff)
    diffGt0 = np.append(diffGt0[0], diffGt0)
    diffABS = np.append(diffABS[0], diffABS)
    rsi = map(lambda x: SMA_CN(diffGt0[:x], timeperiod) / SMA_CN(diffABS[:x], timeperiod) * 100,
              range(1, len(diffGt0) + 1))
    rsi = np.array(rsi)
    return rsi[::-1]


def KDJ_CN(high, low, close, fastk_period, slowk_period, fastd_period):
    high = high[::-1]
    low = low[::-1]
    close = close[::-1]
    kValue, dValue = ta.STOCHF(high, low, close, fastk_period, fastd_period=1, fastd_matype=0)
    kValue = np.nan_to_num(kValue)
    dValue = np.nan_to_num(dValue)
    kValue = np.array(map(lambda x: SMA_CN(kValue[:x], slowk_period), range(1, len(kValue) + 1)))
    dValue = np.array(map(lambda x: SMA_CN(kValue[:x], fastd_period), range(1, len(kValue) + 1)))
    jValue = 3 * kValue - 2 * dValue
    func = lambda arr: np.array([0 if x < 0 else (100 if x > 100 else x) for x in arr])
    kValue = func(kValue)[::-1]
    dValue = func(dValue)[::-1]
    jValue = func(jValue)[::-1]
    return kValue, dValue, jValue
