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


def get_code_filter_list(avg_days = 10, file = None):
    start_time = time.time()
    totals = {}
    list = ts.get_code_list(totals)
    result_list = []
    for code in list:
        # print("Processing code: %s" % code)
        count = 2
        while count > 0:
            try:
                if count == 2:
                    df = ts.get_historic_price(code)
                else:
                    df = ts.get_h_data(code)

                prices = df['close'][0:2 * avg_days]
                if len(prices) <= 0:
                    break

                if prices[0] * totals[code] < 100:
                    break

                avgs = avg(prices, avg_days)
                avg10 = numpy.mean(prices[0:avg_days])

                if prices[0] < min(df['close'][0:2*avg_days])*1.1:
                    break

                if prices[0] < avg10*0.98 or prices[0] > avg10*1.02:
                    break

                if max(df['high'][0:6]) > min(df['low'][0:6])*1.6 or max(df['close'][0:6]) > min(df['close'][0:6])*1.4:
                    break

                if numpy.mean(df['volume'][0:3]) < numpy.mean(df['volume'][0:6])*1.0:
                    break

                zhengfus = get_zheng_fu(df, avg_days)
                if numpy.mean(zhengfus[0:6]) < 2 or numpy.mean(zhengfus[0:6]) > 12:
                    break

                count -= 1
            except Exception as e:
                logger.error("Failed to process code: %s, exception:%s" % (code,e ))
                break
        if count <= 0:
            print("\navgs of %s: %s" % (code, avgs))
            print("zhengfus of %s: %s" % (code, zhengfus))
            result_list.append(code)

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
