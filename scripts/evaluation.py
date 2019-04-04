import tushare as ts
import numpy
from auto_deal_THS import get_direction_by_rsi
from auto_deal_THS import getRSI
from tushare_api import TushareAPI

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)

total_available_money = 30000
max_buy_money = 5000
full_sell_money = 6000

class Stock:
    def __init__(self, code):
        self.code = code
        self.positions = []
        self.prices = []
        self.values = []
        self.actions = []
        self.amounts = []
        self.increases = []
        self.dates = []
        self.returns = []
        self.initial_price = 0
        self.total_position = 0
        self.free_money = total_available_money

    def test(self):
        df = ts.pro_bar(pro_api=pro, ts_code=self.code, adj="qfq")
        start_index = 1800
        if len(df['close'])-26 < start_index:
            start_index = len(df['close'])-26
        self.initial_price = df['close'][start_index]
        for i in range(start_index, -1, -1):
            self.deal(df['close'][i:], df['trade_date'][i])

    def print_as_csv(self, file):
        last_index = len(self.returns)-1
        if self.returns[last_index] - self.increases[last_index] < 1 or self.returns[last_index] < 2:
            return
        writer = open(file, "w")
        writer.write(",price,action,amount,value,price_increase,value_return\n")
        for i in range(len(self.returns)):
            writer.write("%s,%.2f,%s,%d,%.2f,%.2f,%.2f\n" %
                         (self.dates[i], self.prices[i], self.actions[i], self.amounts[i], self.values[i],
                          self.increases[i], self.returns[i]))
        writer.close()

    def deal(self, prices, trade_date):
        direction = get_direction_by_rsi(self.code, prices, 24, False)
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


def test(code):
    stock = Stock(code)
    stock.test()
    stock.print_as_csv("../analyze/filter/returns_%s.csv" % code)


ts_local = TushareAPI()
for code in ts_local.get_code_list():
    code = code.strip()
    if int(code) < 600000:
        code = "%s.SZ" % code
    else:
        code = "%s.SH" % code
    try:
        test(code)
    except Exception as e:
        print "%s" % e
