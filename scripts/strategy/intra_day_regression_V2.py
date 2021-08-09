#!/bin/env python
# -*- coding: utf-8 -*-
import datetime
import math
import traceback

import numpy
import pandas as pd

import scripts.ts_cli as ts
from scripts.bs_volume import get_sell_vol, get_buy_vol
from scripts.file_locator import get_path
from scripts.strategy.intra_day_phiary import IntraDayPhiary
from scripts.strategy.intra_day_dual_thrust import IntraDayDualThrust
from scripts.strategy.intra_day_compose import IntraDayCompose


class IntraDayRegressionSingle:
    def __init__(self, strategy, code, initial_money=20000):
        self.strategy = strategy
        self.final_list = []
        self.code = code
        self.initial_money = initial_money
        self.free_money = self.initial_money
        self.volume = 0
        self.leading_days = 30
        self.last_date = None
        self.buy_fee = 0.0005
        self.sell_fee = 0.0015
        self.start_close = 0
        self.end_close = 0
        self.final_statement = None
        self.daily_values = {}
        self.daily_roes = {}
        self.daily_values_array = []
        self.daily_roes_array = []
        self.roe_total = 0
        self.roe_per_year = 0
        self.sharp_ratio = 0
        self.max_drawdown = 0

    def update_position(self, response, close, date):
        direction = response[0]
        if direction != "N":
            print("code=%s, date=%s, direction=%s" % (self.code, date, direction))
        if direction == "B":
            buy_price = response[1]
            max_cost = self.free_money * (1 - self.buy_fee)
            if self.volume == 0:
                max_cost = max_cost / 2
            buy_vol = get_buy_vol(buy_price, self.volume, max_cost)
            if buy_vol * buy_price < self.free_money:
                if self.volume == 0:
                    # Open position
                    self.volume = self.volume + buy_vol
                    self.free_money = self.free_money - buy_price * buy_vol * (1 + self.buy_fee)
                else:
                    # Update intra day deal profit
                    intra_day_profit = buy_vol * (close * (1 - self.buy_fee - self.sell_fee) - buy_price)
                    self.free_money = self.free_money + intra_day_profit
        if direction == "S":
            sell_price = response[1]
            sell_vol = get_sell_vol(self.volume, sell_price)
            self.volume = self.volume - sell_vol
            self.free_money = self.free_money + sell_vol * sell_price * (1 - self.sell_fee)
        close_value = self.free_money + self.volume * close
        self.daily_values[date] = close_value
        daily_roe = (close_value - self.initial_money)/self.initial_money
        self.daily_roes[date] = daily_roe
        self.daily_values_array.append(close_value)
        self.daily_roes_array.append(daily_roe)
        self.last_date = date
        if close_value < numpy.max(self.daily_values_array):
            self.max_drawdown = (close_value - numpy.max(self.daily_values_array))/numpy.max(self.daily_values_array)

    def update_final_stats(self):
        self.roe_total = self.daily_roes[self.last_date]
        self.roe_per_year = math.pow(1+self.roe_total, 250.0/len(self.daily_roes_array)) - 1
        roe_base = math.pow(1+(self.end_close-self.start_close)/self.start_close, 250.0/len(self.daily_roes_array)) - 1
        var = numpy.var(self.daily_roes_array)
        var_sqrt = numpy.sqrt(var)
        self.sharp_ratio = (self.roe_per_year - roe_base)/var_sqrt
        close_increase = (self.end_close - self.start_close)/self.start_close
        self.final_statement = "%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f" % (self.code, close_increase, self.roe_total,
                                                                           self.roe_per_year, self.max_drawdown,
                                                                           self.sharp_ratio)
        print(self.final_statement)
        print("final position: close_value=%.2f, free_money=%.2f, market_value=%.2f, volume=%d, initial_money=%.2f" %
              (self.daily_values_array[-1], self.free_money, self.daily_values_array[-1] - self.free_money,
               self.volume, self.initial_money))

    def regression(self):
        end_date = (datetime.datetime.now()).strftime("%Y%m%d")
        df_h = ts.get_h_data_cache(self.code, start_date="20160101", end_date=end_date)
        size = len(df_h['close'])
        self.start_close = df_h['close'][size-self.leading_days]
        self.end_close = df_h['close'][1]
        for i in range(size-self.leading_days, 1, -1):
            d = {'price': [0], 'open': [df_h['open'][i]], 'high': [df_h['high'][i]], 'low': [df_h['low'][i]],
                 'volume': [df_h['vol'][i]], 'pre_close': [df_h['close'][i+1]]}
            rt_df = pd.DataFrame(d).reset_index()
            df_h_in = df_h[i+1:].reset_index()
            response = self.strategy.get_direction_extra(rt_df, df_h_in)
            self.update_position(response, df_h['close'][i], df_h['trade_date'][i])


if __name__ == "__main__":
    result_file = get_path("intra_day_regression_V2_results.txt")
    writer = open(result_file, 'w')
    writer.write("code_name\tincr\troe1\troe2\tdown\tsharp\n")
    writer.flush()
    sharp_array = []
    for __code in list(open(get_path("code_candidates.txt"))):
        try:
            code_new = __code.strip()
            if code_new.startswith('0') or code_new.startswith('3'):
                code_new = "%s.SZ" % code_new
            else:
                code_new = "%s.SH" % code_new
            regressionSingle = IntraDayRegressionSingle(IntraDayCompose(), code_new)
            regressionSingle.regression()
            regressionSingle.update_final_stats()
            sharp_array.append(regressionSingle.sharp_ratio)
            writer.write("%s\n" % regressionSingle.final_statement)
            writer.flush()
        except Exception as exe:
            track = traceback.format_exc()
            print(track)
    writer.write("average sharp ratio: %.2f\n" % numpy.mean(sharp_array))
    writer.close()
