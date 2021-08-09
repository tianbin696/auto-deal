#!/bin/env python
import unittest

from scripts.strategy.talib_util import *
from tests.ts_cli_util import get_h_data_cache


class TalibUtilTest(unittest.TestCase):
    def test_rsi_cn(self):
        df = get_h_data_cache("601100", "20210803")
        rsi = RSI_CN(df['close'][0:100], 12)
        rsi = np.nan_to_num(rsi)
        self.assertEqual("70.69", "%.2f" % rsi[0])
        self.assertEqual("67.85", "%.2f" % rsi[1])

    def test_kdj_cn(self):
        df = get_h_data_cache("601100", "20210803")
        k, d, j = KDJ_CN(df['high'][0:100], df['low'][0:100], df['close'][0:100], 9, 3, 3)
        self.assertEqual("73.32", "%.2f" % k[0])
        self.assertEqual("63.71", "%.2f" % d[0])
        self.assertEqual("92.54", "%.2f" % j[0])
