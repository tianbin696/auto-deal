import tushare as ts
import numpy
import time

from auto_deal_THS import get_direction_by_rsi
from auto_deal_THS import get_direction_by_avg
from auto_deal_THS import getRSI
from tushare_api import TushareAPI

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)

total_available_money = 30000
max_buy_money = 5000
full_sell_money = 6000

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
        df = ts.pro_bar(pro_api=pro, ts_code=self.code, adj="qfq")
        start_index = len(df['close'])-26
        self.initial_price = 0
        for i in range(start_index, -1, -1):
            if int(df['trade_date'][i]) >= end_date:
                break
            if int(df['trade_date'][i]) >= start_date:
                if self.initial_price == 0:
                    self.initial_price = df['close'][i]
                self.deal(df['close'][i:], df['trade_date'][i])

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

    def deal(self, prices, trade_date):
        # direction = get_direction_by_rsi(self.code, prices, 24, False)
        direction = get_direction_by_avg(self.code, prices, False)
        amount = 0
        if direction == "S":
            sell_amount = self.get_sell_amount(prices[0])
            if self.total_position >= sell_amount:
                self.total_position -= sell_amount
                self.free_money += sell_amount * prices[0]
                amount = sell_amount
                print "code=%s, trade_date=%s, price=%.2f, direction=%s, amount=%d" % (self.code, trade_date, prices[0], direction, sell_amount)
        if direction == "B":
            buy_amount = self.get_buy_amount(prices[0])
            if self.free_money >= buy_amount * prices[0]:
                self.total_position += buy_amount
                self.free_money -= buy_amount * prices[0]
                amount = buy_amount
                print "code=%s, trade_date=%s, price=%.2f, direction=%s, amount=%d" % (self.code, trade_date, prices[0], direction, buy_amount)
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
        return int(max_buy_money/100/price)*100

    def get_sell_amount(self, price):
        if self.total_position * price > 2 * full_sell_money:
            return max(int(self.total_position/300)*100, 100)
        else:
            return max(int(self.total_position/200)*100, 100)


def test(code, start_date=20100101, end_date=20200101, expect_diff=1.0, expect_return=1.5):
    stocks = []
    found = True
    for date in range(start_date, end_date, end_date):
        stock = Stock(code, expect_diff, expect_return, date)
        stock.test(date, end_date)
        last_index = len(stock.returns)-1
        if last_index > 60:
            # if stock.returns[last_index] - stock.increases[last_index] < stock.expect_diff \
            #         or stock.returns[last_index] < stock.expect_return \
            #         or numpy.max(stock.increases) - numpy.max(stock.returns) > 2*stock.expect_diff:
            #     found = False
            #     break
            stocks.append(stock)
    if found:
        for stock in stocks:
            stock.print_as_csv("../analyze/%s_%s.csv" % (code, stock.start_date))


def get_all_codes():
    writer = open('../analyze/all_codes.txt', 'w')
    ts_local = TushareAPI()
    for code in ts_local.get_code_list():
        code = code.strip()
        if int(code) < 600000:
            code = "%s.SZ" % code
        else:
            code = "%s.SH" % code
        writer.write("%s\n" % code)
    writer.close()


def scan_all():
    ts_local = TushareAPI()
    for code in ts_local.get_code_list():
        code = code.strip()
        if int(code) < 600000:
            code = "%s.SZ" % code
        else:
            code = "%s.SH" % code
        try:
            test(code, 20120101, 0.2, 0.2)
        except Exception as e:
            print "%s" % e


def append_loc(code):
    if code.find("SH") >= 0 or code.find("SZ") >= 0:
        return code
    if int(code) < 600000:
        code = "%s.SZ" % code
    else:
        code = "%s.SH" % code
    return code


def scan_filtered():
    for code in list(open("../codes/candidates.txt")):
        code = append_loc(code.strip())
        test(code, 20140101, 20190101, 0.5, 0.5)


scan_filtered()
