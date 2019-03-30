import tushare as ts
import numpy
from macd import get_MACD

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)


def test_api():
    df = ts.pro_bar(pro_api=pro, ts_code='002797.SZ', adj='qfq')
    df2 = ts.get_realtime_quotes('002797')

    print df2
    print df.head()


def test_liang_bi(code):
    df = ts.pro_bar(pro_api=pro, ts_code=code, adj="qfq")
    for i in range(120):
        price = df['close'][i]
        direction = get_direction_by_rsi(df['close'][i:], 14)

        if direction == 'S':
            print "trade_date=%s: price=%.2f, sell" % (df['trade_date'][i], price)
        if direction == 'B':
            print "trade_date=%s: price = %.2f, buy" % (df['trade_date'][i], price)


def get_direction_by_rsi(prices, days=14):
    if prices[0] > numpy.mean(prices[1:21]):
        buy_value = 50
        sell_value = 80
    elif prices[0] > numpy.mean(prices[1:31]):
        buy_value = 40
        sell_value = 75
    elif prices[0] > numpy.mean(prices[1:61]):
        buy_value = 30
        sell_value = 70
    else:
        buy_value = 20
        sell_value = 65
    rsi = getRSI(prices, days)
    rsi_1 = getRSI(prices[1:], days)
    if rsi < sell_value < rsi_1:
        return 'S'
    if rsi > buy_value > rsi_1:
        return 'B'
    return 'N'


def getRSI(prices, days=14):
    positiveSum = 0
    positiveCount = 0
    negativeSum = 0
    negativeCount = 0
    totalSum = 0
    for i in range(0, days):
        increase = (prices[i] - prices[i + 1]) / prices[i + 1]
        if increase > 0:
            positiveSum += increase
            positiveCount += 1
        else:
            negativeSum += increase
            negativeCount += 1
    result = ((positiveSum) * 100) / ((positiveSum + abs(negativeSum)))
    return int(result)


test_liang_bi("000799.SZ")
