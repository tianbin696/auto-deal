#!/bin/env python
# -*- coding: utf-8 -*-

import math
import numpy
from tushare_api import TushareAPI
import logging
import time
from datetime import datetime
from datetime import timedelta
from concurrent import futures
from collections import OrderedDict

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
    while i < 3:
        if df['volume'][i] > numpy.mean(df['volume'][i:(i+avg_days)])*1.6 and df['close'][i] < df['close'][i+1] * 0.99:
            result = True
            break
        i += 1
    return result


def fang_liang_shang_zhang(df, avg_days=10):
    result = False
    i = 0
    while i < int(avg_days/2):
        if df['volume'][i] > numpy.mean(df['volume'][i:(i+avg_days)])*1.5 and df['close'][i] > df['close'][i+1] * 1.02:
            result = True
            break
        i += 1
    return result


def load_cache(timeStr=None, threadNum=10):
    executor = futures.ThreadPoolExecutor(max_workers=threadNum)
    codes = ts.get_code_list()
    for code in codes:
        print("Submit code: %s" % code)
        executor.submit(ts.get_h_data, code, timeStr=timeStr)
    executor.shutdown(wait=True)
    print("Finish load cache")


def get_code_filter_list(avg_days = 10, file = None, daysAgo = 0, timeStr=None):
    if not timeStr:
        timeStr = time.strftime("%Y%m%d", time.localtime())
    start_time = time.time()
    totals = {}
    shizhi = {}
    liutongs = {}
    list = ts.get_code_list(totals, liutongs)
    result_list = []

    writer = None
    if file:
        writer = open(file, "w")

    for code in list:
        try:
            df = ts.get_h_data(code, timeStr, daysAgo)
            if len(df) < avg_days:
                continue

            prices = df['close']
            avgs = avg(prices, avg_days)
            avg10 = numpy.mean(prices[0:avg_days])
            avg20 = numpy.mean(prices[0:2*avg_days])
            shizhi[code] = totals[code]*prices[0]

            if totals[code]*prices[0] < 1:
                continue
            if prices[0] <= 0 or df['high'][0]*0.96 > prices[0] or prices[0] < avg10 or prices[0] > avg10*1.04:
                continue
            if numpy.mean(df['volume'][0:avg_days]) < numpy.mean(df['volume'][0:2*avg_days])*1.1:
                continue
            if max(df['close'][0:avg_days]) < min(df['close'][0:avg_days])*1.06 or max(df['close'][0:avg_days]) > min(df['close'][0:avg_days])*1.30:
                continue

            # 缩量下跌
            if prices[0] > prices[1] or prices[0] > df['open'][0] or prices[0] < prices[1]*0.96:
                continue
            if df['volume'][0] > numpy.mean(df['volume'][0:avg_days])*0.5:
                continue
            if fang_liang_xia_die(df, avg_days):
                continue

            # 放量上涨
            # if prices[0] < prices[1]*1.01:
            #     continue
            # if df['volume'][0] < numpy.mean(df['volume'][0:avg_days])*1.5:
            #     continue


            # 基于短期价格趋势筛选
            # if prices[0] < max(df['high'][0:avg_days])*0.9:
            #     continue
            #
            # if min(df['low'][0:avg_days]) > max(df['high'][0:avg_days])*0.9 or min(df['low'][0:avg_days]) < max(df['high'][0:avg_days])*0.8:
            #     continue
            #
            # if prices[0] <= min(prices[0:avg_days]) or min(prices[0:avg_days]) < min(prices[0:4 * avg_days])*1.1:
            #     continue
            #
            # if numpy.mean(df['volume'][0:avg_days]) < numpy.mean(df['volume'][0:2*avg_days])*1.2:
            #     continue
            #
            # huanshous = get_huan_shou(df, totals[code], avg_days)
            # if numpy.mean(huanshous) < 1:
            #     continue
            #
            # zhengfus = get_zheng_fu(df, avg_days)
            # if numpy.mean(zhengfus) < 4:
            #     continue
            #
            # if fang_liang_xia_die(df, avg_days):
            #     continue

            print("\navgs of %s: %s" % (code, avgs))
            result_list.append(code)
            if writer:
                writer.write(code + "\n")
                writer.flush()
        except Exception as e:
            logger.error("Failed to process code: %s, exception:%s" % (code,e ))
            continue

    if file:
        writer.close()

    sortedCodes = sort_codes(result_list, avg_days, timeStr, daysAgo)
    if file:
        writer = open(file, 'w')
        for code in sortedCodes[0:10]:
            writer.write(code + "\n")
        writer.close()
    end_time = time.time()
    print("Get %d filter code from total %d codes. Total cost %d seconds" % (len(result_list), len(list), (end_time - start_time)))
    return sortedCodes[0:10]


def sort_codes(codes, avg_days, timeStr=None, daysAgo=0):
    scores = {}
    scores_detail = {}
    for code in codes:
        df = ts.get_h_data(code, timeStr=timeStr, daysAgo=daysAgo)
        volume = df['volume'][0]
        volume_avg5 = numpy.mean(df['volume'][0:int(avg_days/2)])
        volume_avg10 = numpy.mean(df['volume'][0:avg_days])
        volume_avg20 = numpy.mean(df['volume'][0:2*avg_days])
        volume_avg40 = numpy.mean(df['volume'][0:4*avg_days])
        price = df['close'][0]
        lowest = min(df['close'][0:int(avg_days/2)])
        highest = max(df['close'][0:int(avg_days/2)])
        price_avg10 = numpy.mean(df['close'][0:avg_days])
        price_avg20 = numpy.mean(df['close'][0:2*avg_days])

        score0 = highest/price
        score1 = 0
        score2 = price/price_avg10
        score3 = 0
        score4 = 0
        score5 = 0
        score6 = 0
        score7 = 0

        scores[code] = float("%.2f" % (score0 + score1 + score2 + score3 + score4 + score5 + score6 + score7))
        scores_detail[code] = "%.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f" % \
                              (score0, score1, score2, score3, score4, score5, score6, score7)
    sorted_scores = OrderedDict(sorted(scores.items(), key=lambda t: t[1], reverse=True))
    print("Scores: %s" % sorted_scores)
    for code in sorted_scores.keys():
        print("%s: [%s]" % (code, scores_detail[code]))
    new_codes = []
    new_codes.extend(sorted_scores.keys())
    return new_codes


def save_all_codes():
    list = ts.get_code_list()
    writer = open("code_all.csv", "w")
    for code in sorted(list):
        writer.write(code + "\n")
    writer.close()


def verify(codes, daysAgo, timeStr):
    if daysAgo < 3:
        return
    for code in codes:
        df = ts.get_h_data(code, timeStr)
        buyPrice = df['low'][daysAgo-1]*1.02
        max_increase = float("%.2f" % ((max(df['high'][0:(daysAgo-2)])-buyPrice)/buyPrice*100))
        min_increase = float("%.2f" % ((min(df['low'][0:(daysAgo-2)])-buyPrice)/buyPrice*100))
        print("%s increase at %s: [%.2f, %.2f]" % (code, df['date'][daysAgo], min_increase, max_increase))

if __name__ == "__main__":
    avgDays = 12
    timeStr=None

    # 自动筛选+人工审核过滤
    codes = get_code_filter_list(avgDays, "codes.txt", timeStr=timeStr)

    daysAgo = 10
    # codes = get_code_filter_list(avgDays, None, daysAgo, timeStr=timeStr)
    # verify(codes, daysAgo, timeStr)
