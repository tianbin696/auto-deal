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
