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
        self.close_increase = 0
        self.buy_count = 0
        self.sell_count = 0

    def update_position(self, response, close, date):
        direction = response[0]
        if direction != "N":
            print("code=%s, date=%s, direction=%s" % (self.code, date, direction))
        if direction == "B":
            self.buy_count = self.buy_count + 1
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
            self.sell_count = self.sell_count + 1
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
        self.close_increase = (self.end_close - self.start_close)/self.start_close
        self.final_statement = "%s\t%.2f\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f" % (self.code, self.close_increase,
                                                                                self.buy_count, self.sell_count,
                                                                                self.roe_total, self.roe_per_year,
                                                                                self.max_drawdown, self.sharp_ratio)
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


class IntraDayRegressionCompose:
    def __init__(self, codes=None):
        self.codes = []
        self.increases = []
        self.roe_totals = []
        self.roe_per_years = []
        self.sharp_ratios = []
        self.max_dropdowns = []
        self.buy_counts = []
        self.sell_counts = []
        if not codes:
            for code in list(open(get_path("code_candidates.txt"))):
                self.codes.append(code.strip())
        else:
            self.codes = codes

    def get_candidates(self):
        result_file = get_path("intra_day_regression_V2_results.txt")
        writer = open(result_file, 'w')
        writer.write("code_name\tincr\tbuy\tsell\troe1\troe2\tdown\tsharp\n")
        writer.flush()
        code_res = []
        for code in self.codes:
            try:
                code_new = code.strip()
                if code_new.startswith('0') or code_new.startswith('3'):
                    code_new = "%s.SZ" % code_new
                else:
                    code_new = "%s.SH" % code_new
                regression_single = IntraDayRegressionSingle(IntraDayCompose(), code_new)
                regression_single.regression()
                regression_single.update_final_stats()
                code_res.append(code.strip())
                self.increases.append(regression_single.close_increase)
                self.roe_totals.append(regression_single.roe_total)
                self.roe_per_years.append(regression_single.roe_per_year)
                self.sharp_ratios.append(regression_single.sharp_ratio)
                self.max_dropdowns.append(regression_single.max_drawdown)
                self.buy_counts.append(regression_single.buy_count)
                self.sell_counts.append(regression_single.sell_count)
                writer.write("%s\n" % regression_single.final_statement)
                writer.flush()
            except Exception as exe:
                track = traceback.format_exc()
                print(track)
        writer.write("aver_info\t%.2f\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\n" % (float(numpy.mean(self.increases)),
                                                                                int(numpy.mean(self.buy_counts)),
                                                                                int(numpy.mean(self.sell_counts)),
                                                                                float(numpy.mean(self.roe_totals)),
                                                                                float(numpy.mean(self.roe_per_years)),
                                                                                float(numpy.mean(self.max_dropdowns)),
                                                                                float(numpy.mean(self.sharp_ratios))))
        writer.close()
        return code_res


if __name__ == "__main__":
    # regression = IntraDayRegressionCompose(codes=["300433", "300676"])
    regression = IntraDayRegressionCompose()
    regression.get_candidates()
