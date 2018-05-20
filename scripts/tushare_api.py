#!/bin/env python
import tushare as ts
import logging

FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger('TushareAPI')

class TushareAPI:
    def get_historic_price(self, code):
        try:
            df = ts.get_hist_data(code)
            if 'close' in df:
                return df['close']
        except Exception as e:
            logger.error("Failed to get historical price for %s: %s" % (code, e))
        return []

    def get_code_list(self):
        stock_codes = []
        fs = ts.get_stock_basics()
        for code in fs.index:
            if code < '300000' or code >= '600000':
                stock_codes.append(code)
        return stock_codes