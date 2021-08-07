#!/bin/env python
# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from scripts.strategy.intra_day_dual_thrust import IntraDayDualThrust
from tests.ts_cli_util import get_h_data_cache


class IntraDayDualThrustTest(unittest.TestCase):
    def setUp(self):
        self.strategy = IntraDayDualThrust()

    def buy_sell_util(self, df):
        d = {'price': [0], 'open': [df['open'][0]], 'high': [df['high'][0]], 'low': [df['low'][0]],
             'volume': [df['vol'][0]], 'pre_close': [df['close'][1]]}
        __rt_df = pd.DataFrame(d).reset_index()
        __df = df[1:].reset_index()
        __direction = self.strategy.get_direction_extra(__rt_df, __df)
        return __direction[0]

    def test_buy_1(self):
        df = get_h_data_cache("601100", "20210803")
        __direction = self.buy_sell_util(df)
        self.assertEqual(__direction, "N")

    def test_buy_2(self):
        df = get_h_data_cache("601100", "20210802")
        __direction = self.buy_sell_util(df)
        self.assertEqual(__direction, "B")

    def test_sell_1(self):
        df = get_h_data_cache("601100", "20210222")
        __direction = self.buy_sell_util(df)
        self.assertEqual(__direction, "S")
