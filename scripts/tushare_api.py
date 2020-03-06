#!/bin/env python
# -*- coding: utf-8 -*-
import tushare as ts
import logging
import time
import pandas as pd
import os.path
import os
import pandas
import numpy
from datetime import datetime
from datetime import timedelta

token = "cd2026ad7373788082deede38ff419cd87415f50c24322819b71a002"
ts.set_token(token)

logger = logging.getLogger('TushareAPI')
cacheFolder = "../../cache"
cache = {}

class TushareAPI:
    def get_historic_price(self, code):
        try:
            return ts.get_hist_data(code)
        except Exception as e:
            logger.error("Failed to get historical price for %s: %s" % (code, e))
        return []

    def get_h_data(self, code, timeStr = None, daysAgo = 0, do_cache=False):
        if not timeStr:
            timeStr = time.strftime("%Y%m%d", time.localtime())
        cacheFile = cacheFolder + "/" + timeStr + "/" + code + "_" + timeStr + ".csv"
        if not os.path.exists(cacheFolder + "/" + timeStr):
            os.mkdir(cacheFolder + "/" + timeStr)
        if do_cache and cacheFile in cache:
            return cache[cacheFile]

        if os.path.exists(cacheFile):
            df = pandas.read_csv(cacheFile)
        else:
            df = ts.pro_bar(ts_code=code, adj="qfq", retry_count=3)
            if len(df) > 0:
                writer = open(cacheFile, "w")
                df.to_csv(writer)
                writer.close()
            df = pandas.read_csv(cacheFile)
        df = df[daysAgo:].reset_index()
        if do_cache:
            cache[cacheFile] = df
        return df

    def getRSI(self, prices, days=14):
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

    def get_lianban_list(self, timeStr=None, index=0, do_cache=False):
        codes = []
        index_df = self.get_index_h_data("399001.SZ", do_cache=True)
        # if index_df['close'][index] < numpy.mean(index_df['close'][index:index+30]):
        #     return codes

        path="../codes/all_codes.txt"
        for code in list(open(path)):
            code_without_loc = code.strip()
            code = self.append_loc(code.strip())
            try:
                if not timeStr:
                    timeStr = self.get_last_business_day()
                cacheFile = cacheFolder + "/" + timeStr + "/" + code + "_" + timeStr + ".csv"
                if not os.path.exists(cacheFile):
                    continue
                df = self.get_h_data(code, timeStr=timeStr, do_cache=do_cache)
                if len(df['close']) <= index:
                    continue
                if max(max(df['open'][index], df['close'][index+1])*1.04, df['high'][index]*0.96) \
                        <= df['close'][index] <= numpy.min(df['close'][index:index+30])*1.20 \
                        and numpy.mean(df['amount'][index:index+6])*2.0 >= numpy.mean(df['amount'][index:index+3]) \
                        >= numpy.mean(df['amount'][index:index+6])*1.50 \
                        and numpy.mean(df['close'][index:index+5]) > numpy.mean(df['close'][index:index+10]):
                    codes.append(code_without_loc)
            except Exception as e:
                continue
        return codes


    def get_st_list(self):
        fs = ts.get_st_classified()
        codes = []
        for code in fs['code']:
            codes.append(code)
        return codes

    def get_code_list(self, totals={}, liutongs={}):
        st_codes = self.get_st_list()

        stock_codes = []
        fs = ts.get_stock_basics()
        id = -1
        for code in fs.index:
            id += 1
            if code in st_codes:
                continue
            # if fs['pe'][id] < 0 or fs['pe'][id] > 100 or fs['pb'][id] > 20:
            #     continue
            # if fs['rev'][id] < 0 or fs['profit'][id] < 0 or fs['gpr'][id] < 0 or fs['npr'][id] < 0:
            #     continue
            if code < '300000' or code >= '600000':
                stock_codes.append(code)
                totals[code] = fs['totals'][id]
                liutongs[code] = fs['outstanding'][id]
        return sorted(stock_codes)

    def get_realtime_quotes(self, code):
        return ts.get_realtime_quotes(code)


    def get_sina_dd(self, code, timeStr):
        df = ts.get_sina_dd(code, date=timeStr)
        ndf = pandas.DataFrame()
        if df is not None:
            ndf = df.groupby('type').sum().reset_index()
            if len(ndf) > 2:
                return ndf[1:].reset_index()
        return ndf


    def get_fangliang_time(self, code, timeStr=None):
        if not timeStr:
            timeStr = time.strftime("%Y-%m-%d", time.localtime())
        df = ts.get_sina_dd(code, date=timeStr)
        if len(df) < 20:
            return None
        index = len(df)-20
        while index > 0:
            ndf = df[index:].groupby(['type']).sum().reset_index()
            if(ndf['volume'][1] > ndf['volume'][2]*1.5):
                print(ndf)
                return df['time'][index]
            index -= 1
        return None

    def append_loc(self, code):
        if code.find("SH") >= 0 or code.find("SZ") >= 0:
            return code
        if int(code) < 600000:
            code = "%s.SZ" % code
        else:
            code = "%s.SH" % code
        return code

    def get_last_business_day(self):
        data_folder = "../../cache/"
        files = [v for v in os.listdir(data_folder)]
        files.sort()
        last_day = files[-1]
        today_str = time.strftime("%Y%m%d", time.localtime())
        if last_day == today_str:
            # yesterday = (datetime.now() - timedelta(days = 1))
            # last_day = yesterday.strftime("%Y%m%d")
            last_day = files[-1]
        return last_day

    def update_h_data(self, time_str=None):
        path="../codes/all_codes.txt"
        for code in list(open(path)):
            try:
                code = self.append_loc(code.strip())
                self.get_h_data(code, timeStr=time_str)
            except Exception as e:
                continue

    def get_index_h_data(self, code, do_cache=False):
        if do_cache and code in cache:
            return cache[code]
        df = ts.pro_bar(ts_code=code, asset='I')
        if do_cache:
            cache[code] = df
        return df

    def update_h_data1(self):
        yesterday_str = self.get_last_business_day()
        today_str = time.strftime("%Y%m%d", time.localtime())
        path="../codes/candidates.txt"
        for code in list(open(path)):
            code = self.append_loc(code.strip())
            df = self.get_h_data(code, timeStr=yesterday_str)
            size = len(df['close'])
            d = {'ts_code': df['ts_code'][0:size], 'trade_date': df['trade_date'][0:size],
                 'close': df['close'][0:size].astype('float'), 'high': df['high'][0:size].astype('float'),
                 'low': df['low'][0:size].astype('float'), 'vol': df['vol'][0:size].astype('int'),
                 'open': df['open'][0:size], 'pre_close': df['pre_close'][0:size],
                 'amount': df['amount'][0:size]}
            ndf = pd.DataFrame(d)

            # Extend df
            rt_df = ts.get_realtime_quotes(code[0:6])
            nd2 = {'ts_code': code, 'trade_date': [today_str],
                   'close': rt_df['price'][0:1].astype('float'), 'high': rt_df['high'][0:1].astype('float'),
                   'low': rt_df['low'][0:1].astype('float'), 'vol': [rt_df['volume'][0:1].astype('float')[0]/100],
                   'open': rt_df['open'][0:1], 'pre_close': rt_df['pre_close'][0:1],
                   'amount': [rt_df['amount'][0:1].astype('float')[0]/1000]}
            ndf2 = pd.DataFrame(nd2)

            df = pd.concat([ndf2, ndf]).reset_index()
            cache_file = cacheFolder + "/" + today_str + "/" + code + "_" + today_str + ".csv"
            if not os.path.exists(cacheFolder + "/" + today_str):
                os.mkdir(cacheFolder + "/" + today_str)
            if len(df) > 0:
                writer = open(cache_file, "w")
                df.to_csv(writer)
                writer.close()


if __name__ == "__main__":
    local_ts = TushareAPI()
    # timeStr = time.strftime("%Y%m%d", time.localtime())
    timeStr = local_ts.get_last_business_day()
    print("Time: %s" % timeStr)
    # local_ts.update_h_data(local_ts.get_last_business_day())
    # local_ts.update_h_data(timeStr)
    for i in range(19, -1, -1):
        codes = local_ts.get_lianban_list(timeStr=timeStr, index=i, do_cache=True)
        print("%d-%d: %s" % (i, len(codes), codes))
