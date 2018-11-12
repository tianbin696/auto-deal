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
from macd import get_MACD

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


def getRSI(prices, days=6):
    positiveSum = 0
    positiveCount = 0
    negativeSum = 0
    negativeCount = 0
    totalSum = 0
    for i in range(0, days):
        increase = (prices[i] - prices[i+1])/prices[i+1]
        if increase > 0:
            positiveSum += increase
            positiveCount += 1
        else:
            negativeSum += increase
            negativeCount += 1
    result = ((positiveSum)*100) / ((positiveSum + abs(negativeSum)))
    return int(result)


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
            avg10 = numpy.mean(prices[0:avg_days])
            avg20 = numpy.mean(prices[0:2*avg_days])

            # if totals[code]*prices[0] < 50 or totals[code]*prices[0] > 2000:
            #     continue
            if prices[0] <= 0 or prices[0] >= 60:
                continue

            if numpy.mean(df['volume'][0:1]) > numpy.mean(df['volume'][1:2])*3:
                continue

            if numpy.mean(df['volume'][0:1]) > numpy.mean(df['volume'][1:4])*3:
                continue

            if numpy.mean(df['volume'][0:3]) > numpy.mean(df['volume'][3:9])*2:
                continue

            if prices[0] < numpy.min(prices[0:3])*1.1 or prices[0] > numpy.min(prices[0:6])*1.3:
                continue

            if prices[0] < prices[1]*1.06:
                continue

            # get_MACD(df,12,26,9)
            # if numpy.mean(df['macd'][0:12]) > numpy.mean(df['macd'][0:6]):
            #     continue
            # if df['macd'][0] < 0:
            #     continue
            # if df['macd'][0] < df['macd'][1] or df['macd'][1] < df['macd'][2] or df['macd'][2] < df['macd'][3]:
            #     continue
            #
            # rsi6 = getRSI(df['close'], 6)
            # rsi12 = getRSI(df['close'], 12)
            # if not (40 < rsi12 and rsi12 < rsi6 and rsi6 < 75):
            #     continue
            #
            # print("\ncode=%s:" % (code))
            # print("diff=%.2f, dea=%.2f, macd=%.2f, rsi6=%d, rsi12=%d" % (df['diff'][0], df['dea'][0], df['macd'][0], rsi6, rsi12))
            # print("diff=%.2f, dea=%.2f, macd=%.2f" % (df['diff'][1], df['dea'][1], df['macd'][1]))

            result_list.append(code)
            if writer:
                writer.write(code + "\n")
                writer.flush()
        except Exception as e:
            logger.error("Failed to process code: %s, exception:%s" % (code,e ))
            continue

    if file:
        writer.close()

    sortedCodes = sort_codes(result_list, avg_days, timeStr, daysAgo, shizhi)
    if file:
        writer = open(file, 'w')
        for code in sortedCodes[0:20]:
            writer.write(code + "\n")
        writer.close()

    end_time = time.time()
    print("Get %d filter code from total %d codes. Total cost %d seconds" % (len(result_list), len(list), (end_time - start_time)))
    return sortedCodes


def sort_codes(codes, avg_days, timeStr=None, daysAgo=0, shizhi=None):
    print("Start to do sorting...")
    scores = {}
    scores_detail = {}
    for code in codes:
        df = ts.get_h_data(code, timeStr=timeStr, daysAgo=daysAgo)
        score = numpy.mean(df['volume'][0:1])/numpy.mean(df['volume'][1:4])
        score += 1.0/score
        scores[code] = float("%.2f" % score)
        scores_detail[code] = "%.2f" % score
    sorted_scores = OrderedDict(sorted(scores.items(), key=lambda t: t[1], reverse=True))
    idx = 0
    for code in sorted_scores.keys():
        idx += 1
        print("%s: [%s]" % (code, scores_detail[code]))
        if idx >= 20:
            break
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
        buyPrice = max(df['open'][daysAgo-1], df['low'][daysAgo-1]*1.02)
        max_increase = float("%.2f" % ((max(df['high'][0:(daysAgo-1)])-buyPrice)/buyPrice*100))
        min_increase = float("%.2f" % ((min(df['low'][0:(daysAgo-1)])-buyPrice)/buyPrice*100))
        print("%s increase at %s: [%.2f, %.2f]" % (code, df['date'][daysAgo], min_increase, max_increase))

if __name__ == "__main__":
    avgDays = 10

    yesterday = (datetime.now() - timedelta(days = 5))
    timeStr = yesterday.strftime("%Y%m%d")
    df = ts.get_h_data('002066', timeStr)
    codes = ['600570']
    codes = get_code_filter_list(avgDays, "codes.txt", timeStr=timeStr)
    verify(codes, 3, None)

    # 自动筛选+人工审核过滤
    timeStr=None
    codes = get_code_filter_list(avgDays, "codes.txt", timeStr=timeStr)
