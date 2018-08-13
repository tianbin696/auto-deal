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

            if totals[code]*prices[0] < 50:
                continue
            if prices[0] <= 0 or df['high'][0]*0.96 > prices[0] or prices[0] < prices[1] * 0.98 or prices[0] < avg10*0.98 or prices[0] > avg10*1.02:
                continue
            if numpy.mean(df['volume'][0:avg_days]) < numpy.mean(df['volume'][0:2*avg_days])*1.1:
                continue
            if max(df['close'][0:avg_days]) < min(df['close'][0:avg_days])*1.06 or max(df['close'][0:avg_days]) > min(df['close'][0:avg_days])*1.15:
                continue

            # 缩量下跌
            # if prices[0] > min(df['open'][0], prices[1]) or prices[0] < prices[1]*0.96:
            #     continue
            # if df['volume'][0] > numpy.mean(df['volume'][0:avg_days])*0.8:
            #     continue
            # if fang_liang_xia_die(df, avg_days):
            #     continue

            # 放量上涨
            # if prices[0] < max(prices[1], df['open'][0])*1.01:
            #     continue
            # if df['volume'][0] < numpy.mean(df['volume'][0:avg_days])*1.1:
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

    sortedCodes = sort_codes(result_list, avg_days, timeStr, daysAgo, shizhi)
    if file:
        writer = open(file, 'w')
        for code in sortedCodes[0:10]:
            writer.write(code + "\n")
        writer.close()
    end_time = time.time()
    print("Get %d filter code from total %d codes. Total cost %d seconds" % (len(result_list), len(list), (end_time - start_time)))
    return sortedCodes[0:10]


def sort_codes(codes, avg_days, timeStr=None, daysAgo=0, shizhi=None):
    print("Start to do sorting...")
    scores = {}
    scores_detail = {}
    for code in codes:
        df = ts.get_h_data(code, timeStr=timeStr, daysAgo=daysAgo)
        scores2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        idx = 0
        while idx < 10:
            if df['volume'][idx] > numpy.mean(df['volume'][idx:idx+6])*1.4 and df ['close'][idx] > max(df['open'][idx], df['close'][idx+1])*1.01:
                scores2[idx] = 2
            elif df['volume'][idx] < numpy.mean(df['volume'][idx:idx+6])*0.6 and df ['close'][idx] < min(df['open'][idx], df['close'][idx+1]):
                scores2[idx] = 1
            elif df['volume'][idx] > numpy.mean(df['volume'][idx:idx+6])*1.4 and df ['close'][idx] < min(df['open'][idx], df['close'][idx+1])*0.98:
                scores2[idx] = -2
            idx += 1

        score0 = scores2[0]
        score1 = scores2[1]
        score2 = scores2[2]
        score3 = scores2[3]
        score4 = scores2[4]
        score5 = scores2[5]
        score6 = scores2[6]
        score7 = scores2[7]
        score8 = 0
        score9 = scores2[8]
        score10 = scores2[9]
        if shizhi is not None:
            if shizhi[code] < 100:
                score8 = 1
            elif shizhi[code] < 500:
                score8 = 2
            elif shizhi[code] < 1000:
                score8 = 3
            else:
                score8 = 4

        scores[code] = float("%.2f" % (score0 + score1 + score2 + score3 + score4 + score5 + score6 + score7 + score8 + score9 + score10))
        scores_detail[code] = "%.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f" % \
                              (score0, score1, score2, score3, score4, score5, score6, score7, score9, score10, score8)
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
        buyPrice = df['low'][daysAgo-1]*1.02
        max_increase = float("%.2f" % ((max(df['high'][0:(daysAgo-2)])-buyPrice)/buyPrice*100))
        min_increase = float("%.2f" % ((min(df['low'][0:(daysAgo-2)])-buyPrice)/buyPrice*100))
        print("%s increase at %s: [%.2f, %.2f]" % (code, df['date'][daysAgo], min_increase, max_increase))

if __name__ == "__main__":
    avgDays = 12
    timeStr="20180813"

    # 自动筛选+人工审核过滤
    codes = get_code_filter_list(avgDays, "codes.txt", timeStr=timeStr)

    daysAgo = 10
    codes = get_code_filter_list(avgDays, None, daysAgo, timeStr=timeStr)
    verify(codes, daysAgo, timeStr)
