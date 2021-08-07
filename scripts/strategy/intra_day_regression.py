#!/bin/env python
# -*- coding: utf-8 -*-
import datetime

import numpy
import pandas as pd

import scripts.file_locator as locator
import scripts.ts_cli as ts


class IntraDayRegression:
    def __init__(self, strategy):
        self.strategy = strategy
        self.final_list = []
        self.code_hs_300 = locator.get_path("code_hs_300.txt")
        self.candidates = locator.get_path("code_candidates.txt")

    def get_candidates(self, codes=None):
        counts_all = []
        profits_all = []
        counts_filtered = []
        profits_filtered = []
        if not codes:
            codes = list(open(self.code_hs_300))
        for __code in codes:
            try:
                code_new = __code.strip()
                if code_new.startswith('0') or code_new.startswith('3'):
                    code_new = "%s.SZ" % code_new
                else:
                    code_new = "%s.SH" % code_new
                end_date = (datetime.datetime.now()).strftime("%Y%m%d")
                df = ts.get_h_data_cache(code_new, start_date="20160101", end_date=end_date)
                count = 0
                total_profit = 0
                for i in range(1, 300):
                    d = {'price': [0], 'open': [df['open'][i]], 'high': [df['high'][i]], 'low': [df['low'][i]],
                         'volume': [df['vol'][i]], 'pre_close': [df['close'][i+1]]}
                    __rt_df = pd.DataFrame(d).reset_index()
                    __df = df[i+1:].reset_index()
                    __resp = self.strategy.get_direction_extra(__rt_df, __df)
                    __direction = __resp[0]
                    if __direction == "B":
                        count = count + 1
                        buy_price = __resp[1]
                        profit = (df['close'][i]-buy_price)*100/buy_price
                        total_profit = total_profit + profit
                        print("profit of %s: %s, %%%.2f" % (df['trade_date'][i], __direction, profit))
                avg_profit = total_profit/count
                counts_all.append(count)
                profits_all.append(avg_profit)
                if avg_profit > 0.5 and count > 30 and df['close'][0] < 200:
                    self.final_list.append(__code.strip())
                    counts_filtered.append(count)
                    profits_filtered.append(avg_profit)
                print("code: %s, count: %d, average profit: %%%.2f" % (code_new, count, avg_profit))
                print("final list: %s" % self.final_list)
            except Exception as exe:
                print("error for code %s" % __code)
        print("all counts average: %.2f" % numpy.mean(counts_all))
        print("all profits average: %.2f" % numpy.mean(profits_all))
        print("filtered counts average: %.2f" % numpy.mean(counts_filtered))
        print("filtered profits average: %.2f" % numpy.mean(profits_filtered))
        return self.final_list

    def update_candidates(self):
        if len(self.final_list) > 0:
            writer = open(self.candidates, 'w')
            writer.write(self.final_list[0])
            for __code in self.final_list[1:]:
                writer.write("\n" + __code)
            writer.close()
        print("candidates updated")
