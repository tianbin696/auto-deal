#!/bin/env python
# -*- coding: utf-8 -*-
import tushare as ts
import logging
import time

logger = logging.getLogger('TushareAPI')

class TushareAPI:
    def get_historic_price(self, code):
        try:
            return ts.get_hist_data(code)
        except Exception as e:
            logger.error("Failed to get historical price for %s: %s" % (code, e))
        return []

    def get_h_data(self, code):
        retry = 10
        logger.info("Getting historical data for code: %s" % code)
        while retry > 0:
            try:
                df = ts.get_h_data(code, pause=6)
                break
            except Exception as e:
                logger.error("Failed to get history data")
                time.sleep(60)
                retry -= 1
        return df


    def get_st_list(self):
        codes = []
        fs = ts.get_st_classified()
        for code in fs['code']:
            codes.append(code)
        return codes

    def get_code_list(self):
        st_codes = self.get_st_list()

        stock_codes = []
        fs = ts.get_stock_basics()
        for code in fs.index:
            if code in st_codes:
                continue
            if code < '300000' or code >= '600000':
                stock_codes.append(code)
        return stock_codes

    def get_realtime_quotes(self, code):
        return ts.get_realtime_quotes(code)

if __name__ == "__main__":
    df = ts.get_index()
    print("df: %s" % df)