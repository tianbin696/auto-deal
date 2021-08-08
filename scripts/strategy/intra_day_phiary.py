#!/bin/env python
# -*- coding: utf-8 -*-
import numpy

from scripts.strategy.intra_day_regression import IntraDayRegression


class IntraDayPhiary:
    def __init__(self, days=25):
        self.days = days

    def get_direction(self, rt_df_in, df_h_in):
        __direction = self.get_direction_extra(rt_df_in, df_h_in)[0]
        if __direction != "N":
            return __direction
        return "N"

    def get_direction_extra(self, rt_df_in, df_h_in):
        # 菲阿里四价模型
        price_in = float(rt_df_in['price'][0])
        open_price = float(rt_df_in['open'][0])
        high_price = float(rt_df_in['high'][0])
        low_price = float(rt_df_in['low'][0])
        pre_close = float(rt_df_in['pre_close'][0])
        upper_line = numpy.max(df_h_in['high'][0:self.days])
        lower_line = numpy.min(df_h_in['low'][0:self.days])
        if float(rt_df_in['price'][0]) <= 0:
            # For testing
            price_in = min(max(open_price, numpy.max(df_h_in['high'][0:self.days])) + 0.01, high_price)
        if max(upper_line, open_price) < price_in < pre_close * 1.06:
            # For testing
            buy_price = max(open_price, numpy.max(df_h_in['high'][0:self.days]))
            return ["B", buy_price]
        if float(rt_df_in['price'][0]) <= 0:
            # For testing
            price_in = max(min(lower_line, open_price)-0.01, low_price)
        if price_in < lower_line and price_in < open_price:
            sell_price = min(lower_line, open_price)
            return ["S", sell_price]
        return ["N"]


if __name__ == "__main__":
    strategy = IntraDayPhiary()
    regression = IntraDayRegression(strategy)
    regression.get_candidates()
