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

def get_code_filter_list(avg_days = 10, file = None):
    start_time = time.time()
    list = ts.get_code_list()
    code_score = {}
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

                avgs = avg(prices, avg_days)
                avg10 = numpy.mean(prices[0:avg_days])
                avg20 = numpy.mean(prices)

                if prices[0] < min(df['close'][0:12 * avg_days])*1.2:
                    break

                if avg10 < avg20:
                    # 不考虑10日线在20日线下
                    break

                if prices[0] < avg10 or prices[0] > avg10*1.04 or prices[0] <= min(prices[0:int(avg_days/2)]):
                    break

                if count == 2 and df['v_ma5'][0] < df['v_ma10'][0]:
                    break

                if count ==1 and numpy.mean(df['volume'][0:int(avg_days/2)]) < numpy.mean(df['volume'][0:avg_days]):
                    break

                vars = var(avgs[0:avg_days], avg_days)
                code_score[code] = vars[0]
                if code_score[code] < 2 or code_score[code] > 10:
                    break
                count -= 1
            except Exception as e:
                logger.error("Failed to process code: %s, exception:%s" % (code,e ))
                break
        if count <= 0:
            print("\navgs of %s: %s" % (code, avgs))
            print("vars of %s: %s" % (code, vars))
            result_list.append(code)

    if file:
        writer = open(file, "w")
        score_writer = open("code_score.csv", "w")
        score_writer.write("code,score\n")
        for code in sorted(result_list):
            writer.write(code + "\n")
            score_writer.write("'%s',%.2f\n" % (code, code_score[code]))
        writer.close()
        score_writer.close()

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
