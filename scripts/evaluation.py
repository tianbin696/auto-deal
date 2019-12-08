import tushare as ts
import numpy
import time
import pandas as pd
import os

from datetime import datetime
from datetime import timedelta

from auto_deal_THS import get_direction_by_rsi
from auto_deal_THS import get_direction_by_avg
from auto_deal_THS import get_direction_by_macd
from auto_deal_THS import get_direction_by_composite_ways
from auto_deal_THS import getRSI
from tushare_api import TushareAPI

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)
ts_local = TushareAPI()

total_available_money = 40000

all_returns = []
all_increases = []


class Stock:
    def __init__(self, code, expect_diff=1.0, expect_return=1.5, start_date=20100101):
        self.code = code
        self.positions = []
        self.prices = []
        self.values = []
        self.actions = []
        self.amounts = []
        self.increases = []
        self.dates = []
        self.returns = []
        self.expect_diff = expect_diff
        self.expect_return = expect_return
        self.initial_price = 0
        self.total_position = 0
        self.free_money = total_available_money
        self.start_date = start_date

    def test(self, start_date=20100101, end_date=20200101):
        df = ts_local.get_h_data(self.code)
        # df = ts.pro_bar(pro_api=pro, ts_code=self.code, adj="qfq")
        start_index = len(df['close'])-60
        self.initial_price = 0
        for i in range(start_index, -1, -1):
            if int(df['trade_date'][i]) > end_date:
                break
            if int(df['trade_date'][i]) >= start_date:
                if self.initial_price == 0:
                    self.initial_price = df['close'][i]
                d = {'close':df['close'][i:i+52].astype('float')}
                ndf = pd.DataFrame(d).reset_index()
                self.deal(df['close'][i:].values, df['vol'][i:].values, df['trade_date'][i], ndf, df['open'][i], df['high'][i])

    def print_as_csv(self, file):
        # last_index = len(self.returns)-1
        # if self.returns[last_index] - self.increases[last_index] < self.expect_diff or self.returns[last_index] < self.expect_return:
        #     return
        writer = open(file, "w")
        writer.write(",price,action,amount,value,price_increase,value_return\n")
        for i in range(len(self.returns)):
            writer.write("%s,%.2f,%s,%d,%.2f,%.2f,%.2f\n" %
                         (self.dates[i], self.prices[i], self.actions[i], self.amounts[i], self.values[i],
                          self.increases[i], self.returns[i]))
        writer.close()

    def deal(self, prices, vols, trade_date, df, open_price=0, highest_price=0):
        # direction = get_direction_by_macd(self.code, df)
        # direction = get_direction_by_rsi(self.code, prices, False)
        # direction = get_direction_by_avg(self.code, prices, vols, False, open_price, highest_price)
        direction = get_direction_by_composite_ways(self.code, prices, vols, False, open_price, highest_price)
        amount = 0
        if direction == "S":
            sell_amount = self.get_sell_amount(prices[0])
            if self.total_position >= sell_amount:
                self.total_position -= sell_amount
                self.free_money += sell_amount * prices[0]
                amount = sell_amount
                print("code=%s, trade_date=%s, price=%.2f, direction=%s, amount=%d" % (self.code, trade_date, prices[0], direction, sell_amount))
        if direction == "B":
            buy_amount = self.get_buy_amount(prices[0])
            if self.free_money >= buy_amount * prices[0]:
                self.total_position += buy_amount
                self.free_money -= buy_amount * prices[0]
                amount = buy_amount
                print("code=%s, trade_date=%s, price=%.2f, direction=%s, amount=%d" % (self.code, trade_date, prices[0], direction, buy_amount))
        value = self.total_position * prices[0] + self.free_money
        self.values.append(value)
        self.prices.append(prices[0])
        self.actions.append(direction)
        self.amounts.append(amount)
        self.increases.append((prices[0]-self.initial_price)/self.initial_price)
        self.positions.append(self.total_position)
        self.dates.append(trade_date)
        self.returns.append(float("%.2f" % ((value - total_available_money)/total_available_money)))

    def get_buy_amount(self, price):
        return int(self.free_money/100/price)*100

    def get_sell_amount(self, price):
        return max(int(self.total_position/100)*100, 100)


def save_2_candidates(code):
    path = "../codes/candidates.txt"
    writer = open(path, "a+")
    writer.write("%s\n" % code[0:6])
    writer.close()


def test(code, start_date=20100101, end_date=20200101, expect_return=0.8, expect_diff=0.6, save_to_candidates=True):
    stock = Stock(code, expect_diff, expect_return, start_date)
    stock.test(start_date, end_date)
    last_index = len(stock.returns)-1
    if last_index > 60:
        all_returns.append(stock.returns[last_index])
        all_increases.append(stock.increases[last_index])
        if numpy.isnan(stock.increases[last_index]):
            print("NaN of code: %s" % code)
            exit(1)
        if numpy.max(stock.increases) < 3.0 and numpy.min(stock.returns) > -0.5 and stock.returns[last_index] > 0.5 \
                and numpy.mean(stock.returns) > numpy.mean(stock.increases)*1.5 \
                and stock.returns[last_index] > numpy.max(stock.returns)*0.70:
            if save_to_candidates:
                save_2_candidates(code)
            stock.print_as_csv("../analyze/%s_%s.csv" % (code, stock.start_date))


def get_all_codes():
    writer = open('../codes/all_codes.txt', 'w')
    for code in ts_local.get_code_list():
        code = code.strip()
        # if int(code) < 600000:
        #     code = "%s.SZ" % code
        # else:
        #     code = "%s.SH" % code
        writer.write("%s\n" % code)
    writer.close()


def stats(increases):
    stats = []
    for i in range(0, 12, 1):
        stats.append(0)
    for value in increases:
        try:
            if numpy.isnan(value):
                continue
            if value <= -0.5:
                idx = 0
            elif value <= -0.4:
                idx = 1
            elif value <= -0.3:
                idx = 2
            elif value <= -0.2:
                idx = 3
            elif value <= -0.1:
                idx = 4
            elif value <= 0:
                idx = 5
            elif value <= 0.1:
                idx = 6
            elif value <= 0.2:
                idx = 7
            elif value <= 0.3:
                idx = 8
            elif value <= 0.4:
                idx = 9
            elif value <= 0.5:
                idx = 10
            else:
                idx = 11
            stats[idx] += 1
        except Exception as e:
            print("exception: %s" % e)
    for count in stats:
        print("%d," % count),
    print("\n"),


def append_loc(code):
    if code.find("SH") >= 0 or code.find("SZ") >= 0:
        return code
    if int(code) < 600000:
        code = "%s.SZ" % code
    else:
        code = "%s.SH" % code
    return code


def clear_candidates():
    if os.path.exists('../codes/candidates.txt'):
        os.remove("../codes/candidates.txt")


def scan_all():
    clear_candidates()
    ts_local = TushareAPI()
    endDate = (datetime.now() - timedelta(days = 0))
    endTimeStr = int(endDate.strftime("%Y%m%d"))
    startTimeStr = endTimeStr - 10000
    for code in ts_local.get_code_list():
        code = code.strip()
        if int(code) < 600000:
            code = "%s.SZ" % code
        else:
            code = "%s.SH" % code
        try:
            test(code, startTimeStr, endTimeStr, 0.5, 1.0)
        except Exception as e:
            print("%s" % e)


def scan_filtered(path="../codes/candidates.txt", save_candidates=False):
    endDate = (datetime.now() - timedelta(days = 0))
    endTime = int(endDate.strftime("%Y%m%d"))
    startTime = endTime - 30000
    st_codes = ts_local.get_st_list()
    for code in list(open(path)):
        if code.strip() in st_codes:
            continue
        code = append_loc(code.strip())
        try:
            test(code, startTime, endTime, 1.0, 4.0, save_candidates)
        except Exception as e:
            print("%s" % e)


# get_all_codes()
# scan_all()
# clear_candidates()
# scan_filtered(path="../codes/manual_filtered.txt", save_candidates=True)
del all_increases[:]
del all_returns[:]
scan_filtered()
stats(all_increases)
stats(all_returns)
print("increase avg: %.2f" % numpy.mean(all_increases))
print("return avg: %.2f" % numpy.mean(all_returns))
