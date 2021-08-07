#!/bin/env python
# -*- coding: utf-8 -*-
import numpy
from scripts.strategy.intra_day_regression import IntraDayRegression


class IntraDualThrust:
    def __init__(self, days=20, k1=0.25, k2=0.25):
        self.days = days
        self.k1 = k1
        self.k2 = k2

    def get_direction(self, rt_df_in, df_h_in):
        __direction = self.get_direction_extra(rt_df_in, df_h_in)[0]
        if __direction != "N":
            return __direction
        return "N"

    def get_direction_extra(self, rt_df_in, df_h_in):
        # Dual Thrust
        price_in = float(rt_df_in['price'][0])
        open_price = float(rt_df_in['open'][0])
        high_price = float(rt_df_in['high'][0])
        low_price = float(rt_df_in['low'][0])
        pre_close = float(rt_df_in['pre_close'][0])

        hh = numpy.max(df_h_in['high'][0:self.days])
        lc = numpy.min(df_h_in['close'][0:self.days])
        hc = numpy.max(df_h_in['close'][0:self.days])
        ll = numpy.min(df_h_in['low'][0:self.days])
        __range = max(hh - lc, hc - ll)
        buy_line = open_price + self.k1 * __range
        sell_line = open_price - self.k2 * __range

        if float(rt_df_in['price'][0]) <= 0:
            price_in = min(buy_line + 0.01, high_price)
        if buy_line < price_in < pre_close * 1.06:
            buy_price = buy_line
            return ["B", buy_price]

        if float(rt_df_in['price'][0]) <= 0:
            price_in = max(sell_line - 0.01, low_price)
        if price_in < sell_line:
            return ["S"]

        return ["N"]


if __name__ == "__main__":
    strategy = IntraDualThrust()
    regression = IntraDayRegression(strategy)
    regression.get_candidates()
    regression.update_candidates()
