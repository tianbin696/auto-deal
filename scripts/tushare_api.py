#!/bin/env python
# -*- coding: utf-8 -*-
import tushare as ts
import logging
import time
import os.path
import os
import pandas
from datetime import datetime
from datetime import timedelta

logger = logging.getLogger('TushareAPI')
cacheFolder = "../../cache"

class TushareAPI:
    def get_historic_price(self, code):
        try:
            return ts.get_hist_data(code)
        except Exception as e:
            logger.error("Failed to get historical price for %s: %s" % (code, e))
        return []

    def get_h_data(self, code, timeStr = None, daysAgo = 0):
        retry = 2
        if not timeStr:
            timeStr = time.strftime("%Y%m%d", time.localtime())
        cacheFile = cacheFolder + "/" + timeStr + "/" + code + "_" + timeStr + ".csv"
        if not os.path.exists(cacheFolder + "/" + timeStr):
            os.mkdir(cacheFolder + "/" + timeStr)
        logger.info("Getting historical data for code: %s" % code)

        if os.path.exists(cacheFile):
            df = pandas.read_csv(cacheFile)
        else:
            yesterday = (datetime.now() - timedelta(days = 1))
            yesterdayTimeStr = yesterday.strftime("%Y%m%d")
            yesterdayFilePath = cacheFolder + "/" + yesterdayTimeStr + "/" + code + "_" + yesterdayTimeStr + ".csv"
            if os.path.exists(yesterdayFilePath):
                df = pandas.read_csv(yesterdayFilePath)
                df = pandas.DataFrame({'date':df['date'], 'open':df['open'], 'high':df['high'],
                                       'close':df['close'], 'low':df['low'], 'volume':df['volume'],
                                               'amount':df['amount']}, columns=['date', 'open', 'high', 'close', 'low', 'volume', 'amount'])
                rtDF = ts.get_realtime_quotes(code)
                if float(rtDF['price'][0]) <= 0:
                    print("Invalid price for code = %s: %s" % (code, rtDF['price'][0]))
                elif float(rtDF['price'][0]) > float(df['close'][0]) *1.2 or float(rtDF['price'][0]) < float(df['close'][0]) *0.8:
                    print("Invalid price for code = %s: %s, %s" % (code, rtDF['price'][0], df['close'][0]))
                    df = ts.get_h_data(code, start='2018-06-01', pause=8)
                elif rtDF['date'][0] != df['date'][0]:
                    df.loc[-1] = [rtDF['date'][0], rtDF['open'][0], rtDF['high'][0], rtDF['price'][0], rtDF['low'][0], rtDF['volume'][0], rtDF['amount'][0]]
                    df.index = df.index+1
                    df = df.sort_index()
                if len(df) > 0:
                    writer = open(cacheFile, "w")
                    df.to_csv(writer)
                    writer.close()
                df = pandas.read_csv(cacheFile)
            else:
                df = pandas.DataFrame()
                while retry > 0:
                    try:
                        # df = ts.get_h_data(code, start='2018-06-01', pause=8)
                        # if len(df) > 0:
                        #     writer = open(cacheFile, "w")
                        #     df.to_csv(writer)
                        #     writer.close()
                        break
                    except Exception as e:
                        logger.error("Failed to get history data for code=%s" % code)
                        time.sleep(10)
                        retry -= 1
        return df[daysAgo:].reset_index()


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
        ndf = ts.get_sina_dd(code, date=timeStr).groupby('type').sum().reset_index()
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


if __name__ == "__main__":
    local_ts = TushareAPI()
    code = '002025'
    timeStr = '2018-08-03'
    print("Fangliang time for code=%s: %s" %(code, local_ts.get_fangliang_time(code, timeStr=timeStr)))