#!/bin/env python
# -*- coding: utf-8 -*-
import tushare as ts
import logging
import time
import os.path
import os
import pandas

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
            while retry > 0:
                try:
                    df = ts.get_h_data(code, start='2018-06-01', pause=8)
                    writer = open(cacheFile, "w")
                    df.to_csv(writer)
                    writer.close()
                    break
                except Exception as e:
                    logger.error("Failed to get history data for code=%s" % code)
                    time.sleep(60)
                    retry -= 1
        return df[daysAgo:].reset_index()


    def get_st_list(self):
        fs = ts.get_st_classified()
        codes = []
        for code in fs['code']:
            codes.append(code)
        return codes

    def get_code_list(self, totals={}):
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
        return sorted(stock_codes)

    def get_realtime_quotes(self, code):
        return ts.get_realtime_quotes(code)

if __name__ == "__main__":
    df = ts.get_index()
    print("df: %s" % df)