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

token = "edb4af8baea44c2cd6e02d8e02e81682eb98928475b3f7f67d3ba5f2"
pro = ts.pro_api(token)

logger = logging.getLogger('TushareAPI')
cacheFolder = "../cache"

class TushareAPI:
    def get_historic_price(self, code):
        try:
            return ts.get_hist_data(code)
        except Exception as e:
            logger.error("Failed to get historical price for %s: %s" % (code, e))
        return []

    def get_h_data(self, code, timeStr = None, daysAgo = 0):
        if not timeStr:
            timeStr = time.strftime("%Y%m%d", time.localtime())
        cacheFile = cacheFolder + "/" + timeStr + "/" + code + "_" + timeStr + ".csv"
        if not os.path.exists(cacheFolder + "/" + timeStr):
            os.mkdir(cacheFolder + "/" + timeStr)

        if os.path.exists(cacheFile):
            df = pandas.read_csv(cacheFile)
        else:
            df = ts.pro_bar(ts_code=code, adj="qfq")
            if len(df) > 0:
                writer = open(cacheFile, "w")
                df.to_csv(writer)
                writer.close()
            df = pandas.read_csv(cacheFile)
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


if __name__ == "__main__":
    local_ts = TushareAPI()
    code = '002025'
    timeStr = '2018-08-03'
    print("Fangliang time for code=%s: %s" %(code, local_ts.get_fangliang_time(code, timeStr=timeStr)))