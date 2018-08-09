#!/bin/env python
# -*- coding: utf-8 -*-

import math
import numpy
from tushare_api import TushareAPI
import logging
import time
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
    while i < avg_days:
        if df['volume'][i] > df['volume'][i+1]*2 and df['close'][i] < df['close'][i+1] * 0.96:
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


def get_code_filter_list(avg_days = 10, file = None, daysAgo = 0, timeStr=None, fangLiangDaysAgo=0):
    if not timeStr:
        timeStr = time.strftime("%Y%m%d", time.localtime())
    start_time = time.time()
    totals = {}
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

            if prices[0] <= 0 or prices[0] < avg10*0.98 or prices[0] > avg10*1.02:
                continue

            if totals[code]*prices[0] < 50:
                continue

            # 基于当日成交量和涨幅筛选
            if df['open'][fangLiangDaysAgo] > prices[fangLiangDaysAgo] or df['high'][fangLiangDaysAgo]*0.96 > prices[fangLiangDaysAgo]:
                continue
            if df['volume'][fangLiangDaysAgo] < df['volume'][fangLiangDaysAgo+1]*2 \
                    and df['volume'][fangLiangDaysAgo] < df['volume'][fangLiangDaysAgo+2]*2 \
                    and df['volume'][fangLiangDaysAgo] < df['volume'][fangLiangDaysAgo+3]*2:
                continue
            if df['volume'][fangLiangDaysAgo] < df['volume'][fangLiangDaysAgo+1]:
                continue
            if df['volume'][fangLiangDaysAgo] < numpy.mean(df['volume'][fangLiangDaysAgo:(fangLiangDaysAgo+avg_days)])*1.2:
                continue
            if max(df['high'][0:avg_days]) > min(df['low'][0:avg_days])*1.2:
                continue
            if max(df['close'][0:avg_days]) > min(df['close'][0:avg_days])*1.15:
                continue
            ndf = ts.get_sina_dd(code, df['date'][0])
            if len(ndf) < 2 or ndf['volume'][0] < ndf['volume'][1]*1.5:
                continue

            huanshous = get_huan_shou(df, liutongs[code], avg_days)
            if numpy.sum(huanshous[0:int(avg_days/2)]) < 1.5:
                continue

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
            print(ndf)
            result_list.append(code)
            if writer:
                writer.write(code + "\n")
                writer.flush()
        except Exception as e:
            logger.error("Failed to process code: %s, exception:%s" % (code,e ))
            continue

    if file:
        writer.close()

    sortedCodes = sort_codes(result_list, avg_days, timeStr)
    if file:
        writer = open(file, 'w')
        for code in sortedCodes:
            writer.write(code + "\n")
        writer.close()
    end_time = time.time()
    print("Get %d filter code from total %d codes. Total cost %d seconds" % (len(result_list), len(list), (end_time - start_time)))
    return result_list


def sort_codes(codes, avg_days, timeStr=None):
    scores = {}
    for code in codes:
        df = ts.get_h_data(code, timeStr=timeStr)
        score_volume = max(2-abs(2-df['volume'][0]/numpy.mean(df['volume'[0:avg_days]])), 0)
        price_percentage = (df['close'][0]-df['close'][1])/df['close'][1]*100
        score_price = max(2 - abs(price_percentage-4), 0)
        price_percentage = (df['close'][0]-numpy.mean(df['close'][0:avg_days]))/numpy.mean(df['close'][0:avg_days])*100
        score_avg = max(2 - abs(price_percentage-0), 0)
        scores[code] = float("%.2f" % (score_volume+score_price+score_avg))
    sorted_scores = OrderedDict(sorted(scores.items(), key=lambda t: t[1], reverse=True))
    print("Scores: %s" % sorted_scores)
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
        max_increase = float("%.2f" % ((max(df['high'][0:(daysAgo-2)])-df['close'][daysAgo-1])/df['close'][daysAgo-1]*100))
        min_increase = float("%.2f" % ((min(df['low'][0:(daysAgo-2)])-df['close'][daysAgo-1])/df['close'][daysAgo-1]*100))
        print("%s increase: [%.2f, %.2f]" % (code, min_increase, max_increase))

if __name__ == "__main__":
    avgDays = 12
    timeStr="20180808"
    # load_cache(timeStr, threadNum=4)

    fangLiangDaysAgo = 0
    codes = get_code_filter_list(avgDays, "codes.txt", timeStr=timeStr, fangLiangDaysAgo=fangLiangDaysAgo)

    daysAgo = 10
    # codes = get_code_filter_list(avgDays, None, daysAgo, timeStr=timeStr, fangLiangDaysAgo=fangLiangDaysAgo)
    # verify(codes, daysAgo, timeStr)
