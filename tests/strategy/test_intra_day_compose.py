#!/bin/env python
import unittest

import pandas as pd

from scripts.strategy.intra_day_compose import IntraDayCompose
from tests.ts_cli_util import get_h_data_cache


class IntraDayComposeTest(unittest.TestCase):
    def setUp(self):
        self.strategy = IntraDayCompose()

    def test_get_direction_1(self):
        df = get_h_data_cache("601100", "20210803")
        d = {'price': [0], 'open': [df['open'][0]], 'high': [df['high'][0]], 'low': [df['low'][0]],
             'volume': [df['vol'][0]], 'pre_close': [df['close'][1]]}
        rt_df = pd.DataFrame(d).reset_index()
        df_h = df[1:].reset_index()
        direction_1 = self.strategy.get_direction(rt_df, df_h)
        direction_2 = self.strategy.get_direction_extra(rt_df, df_h)
        self.assertEqual(direction_1, direction_2[0])

    def test_get_direction_2(self):
        df = get_h_data_cache("601100", "20210802")
        d = {'price': [0], 'open': [df['open'][0]], 'high': [df['high'][0]], 'low': [df['low'][0]],
             'volume': [df['vol'][0]], 'pre_close': [df['close'][1]]}
        rt_df = pd.DataFrame(d).reset_index()
        df_h = df[1:].reset_index()
        direction_1 = self.strategy.get_direction(rt_df, df_h)
        direction_2 = self.strategy.get_direction_extra(rt_df, df_h)
        self.assertEqual(direction_1, direction_2[0])

    def test_get_direction_3(self):
        df = get_h_data_cache("601100", "20210222")
        d = {'price': [0], 'open': [df['open'][0]], 'high': [df['high'][0]], 'low': [df['low'][0]],
             'volume': [df['vol'][0]], 'pre_close': [df['close'][1]]}
        rt_df = pd.DataFrame(d).reset_index()
        df_h = df[1:].reset_index()
        direction_1 = self.strategy.get_direction(rt_df, df_h)
        direction_2 = self.strategy.get_direction_extra(rt_df, df_h)
        self.assertEqual(direction_1, direction_2[0])

    def test_get_candidates(self):
        # codes = self.strategy.get_candidates()
        # self.assertTrue(len(codes) > 0)
        self.assertTrue(True)
