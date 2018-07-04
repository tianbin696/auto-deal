#!/bin/env python
# -*- coding: utf-8 -*-

import math
import numpy
from tushare_api import TushareAPI
import logging

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

def get_code_filter_list(avg_days = 10, file = None):
    list = ts.get_code_list()
    code_score = {}
    var_list = []
    for code in list:
        try:
            df = ts.get_historic_price(code)
            prices = df['close'][0:2 * avg_days]
            if len(prices) <= 0 or prices[0] > 15:
                continue

            # if df['volume'][0] < df['v_ma10'][0]:
            #     # 忽略缩量的股票
            #     continue

            avgs = avg(prices, avg_days)

            if avgs[0] < numpy.mean(prices[0:2*avg_days]):  # 不考虑买入10日均线在20日线下的股票，这种为向下趋势
                continue

            if prices[0] > avgs[0] * 1.04:  # 不考虑大于10日线*1.04的股票
                continue

            if prices[0] < avgs[0] * 0.96:  # 不考虑小于10日线*0.96的股票
                continue

            vars = var(avgs[0:avg_days], avg_days)
            code_score[code] = vars[0]
            logger.debug("avgs of %s: %s" % (code, avgs))
            logger.debug("vars of %s: %s" % (code, vars))
            var_list.append(vars[0])
        except Exception as e:
            logger.error("Failed to process code: %s" % code)

    median_value = numpy.median(var_list)
    result = []
    for code in code_score.keys():
        if code_score[code] > 2 and code_score[code] < 10:
            df = ts.get_realtime_quotes(code)
            changePercentage = (float(df['price'][0]) - float(df['pre_close'][0])) / float(df['pre_close'][0])  * 100
            if changePercentage > 4:
                # 前一日涨幅超过4%时不考虑，防止追高被套
                print("Ignore code > 4: %s" % code)
                continue
            if changePercentage < 1:
                # 前一日涨幅小于1%时不考虑
                print("Ignore code < 1: %s" % code)
                continue

            if float(df['open'][0]) > float(df['price'][0]):
                # 不考虑高开低走的股票
                print("Open price > close price: %s" % code)
                continue

            if float(df['high'][0]) > float(df['price'][0]) * 1.04:
                # 不考虑长上影线的股票
                print("High price > close price * 1.04: %s" % code)
                continue
            result.append(code)

    if file:
        writer = open(file, "w")
        score_writer = open("code_score.csv", "w")
        score_writer.write("code,score\n")
        for code in sorted(result):
            writer.write(code + "\n")
            score_writer.write("'%s',%.2f\n" % (code, code_score[code]))
        writer.close()
        score_writer.close()

    print("Get %d filter code from total %d codes" % (len(result), len(list)))
    return result


def save_all_codes():
    list = ts.get_code_list()
    writer = open("code_all.csv", "w")
    for code in sorted(list):
        writer.write(code + "\n")
    writer.close()


if __name__ == "__main__":

    # save_all_codes()

    days = 12
    prices = ts.get_historic_price('000615')['close'][0:2 * days]
    print("avgs: %s" % avg(prices, days))
    print("vars: %s" % var(avg(prices, days)[0:days], days))

    get_code_filter_list(days, "codes.txt")
