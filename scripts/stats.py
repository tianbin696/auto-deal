#!/bin/env python
# -*- coding: utf-8 -*-

import math
import numpy
from tushare_api import TushareAPI
import logging
import time

logger = logging.getLogger('stats')
ts = TushareAPI()


def avg(array, days, return_size = 0):
    """
    :param array: containing close prices
    :param days: days of average
    :param return_size: default size will be 2 * days
    :return: list containing avg
    """
    if return_size == 0:
        return_size = 2 * days
    result = []
    for i in range(return_size):
        result.append(float("%.2f" % numpy.mean(array[i:i+days])))

    return result


def var(array, days, return_size = 0):
    """
    :param array: containing avgs
    :param days: days of var
    :param return_size: default size will be same as days
    :return: list containing var
    """
    if return_size == 0:
        return_size = days

    new_array = []
    max_value = max(array)
    for v in array:
        # 归一化处理，将所有股票价格映射到[0,100]，方便比较方差，从而根据方差来判断价格的波动情况
        new_array.append(v/max_value*100)

    result = []
    for i in range(return_size):
        result.append(float("%.2f" % numpy.var(new_array[i:i+days])))
    return result


def get_zheng_fu(df, avg_days = 10):
    zhengfu = []
    i = 0
    while i < avg_days:
        zhengfu.append(float("%.2f" % ((df['high'][i] - df['low'][i])/df['low'][i]*100)))
        i += 1
    return zhengfu


def get_huan_shou(df, total, avg_days = 10):
    huanshou = []
    i = 0
    while i < avg_days:
        huanshou.append(float("%.2f" % (df['volume'][i]/(total*100000000)*100)))
        i += 1
    return huanshou


def fang_liang_xia_die(df, avg_days=10):
    result = False
    i = 0
    while i < avg_days:
        if df['volume'][i] > df['volume'][i+1]*2 and df['close'][i] < df['close'][i+1] * 0.96:
            result = True
            break
        i += 1
    return result


def get_code_filter_list(avg_days = 10, file = None):
    start_time = time.time()
    totals = {}
    list = ts.get_code_list(totals)
    result_list = []
    for code in list:
        try:
            df = ts.get_h_data(code)
            if len(df) <= 0:
                continue

            prices = df['close'][0:4 * avg_days]
            avgs = avg(prices, avg_days)
            avg10 = numpy.mean(prices[0:avg_days])

            if prices[0] < avg10*0.98 or prices[0] > avg10*1.02:
                continue

            if prices[0] < prices[1]*0.96:
                continue

            if prices[0] < max(df['high'][0:avg_days])*0.9:
                continue

            if min(df['low'][0:avg_days]) > max(df['high'][0:avg_days])*0.85:
                continue

            if prices[0] <= min(prices[0:avg_days]) or min(prices[0:avg_days]) < min(prices[0:4 * avg_days])*1.1:
                continue

            if numpy.mean(df['volume'][0:avg_days]) < numpy.mean(df['volume'][0:2*avg_days])*1.1:
                continue

            huanshous = get_huan_shou(df, totals[code], avg_days)
            if numpy.mean(huanshous) < 1:
                continue

            zhengfus = get_zheng_fu(df, avg_days)
            if numpy.mean(zhengfus) < 4:
                continue

            if fang_liang_xia_die(df, avg_days):
                continue

            print("\navgs of %s: %s" % (code, avgs))
            print("huanshou of %s: %s" % (code, huanshous))
            print("zhengfus of %s: %s" % (code, zhengfus))
            result_list.append(code)
        except Exception as e:
            logger.error("Failed to process code: %s, exception:%s" % (code,e ))
            continue

    if file:
        writer = open(file, "w")
        for code in sorted(result_list):
            writer.write(code + "\n")
        writer.close()

    end_time = time.time()
    print("Get %d filter code from total %d codes. Total cost %d seconds" % (len(result_list), len(list), (end_time - start_time)))
    return result_list


def save_all_codes():
    list = ts.get_code_list()
    writer = open("code_all.csv", "w")
    for code in sorted(list):
        writer.write(code + "\n")
    writer.close()


if __name__ == "__main__":

    # save_all_codes()

    days = 12
    get_code_filter_list(days, "codes.txt")
