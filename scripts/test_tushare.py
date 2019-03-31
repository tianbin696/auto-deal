import tushare as ts
import numpy
from macd import get_MACD
from auto_deal_THS import get_direction_by_rsi

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)


def test_api():
    df = ts.pro_bar(pro_api=pro, ts_code='002797.SZ', adj='qfq')
    df2 = ts.get_realtime_quotes('002797')

    print df2
    print df.head()


def test_action(code):
    df = ts.pro_bar(pro_api=pro, ts_code=code, adj="qfq")
    for i in range(120):
        price = df['close'][i]
        direction = get_direction_by_rsi(code, df['close'][i:], 24, False)

        if direction == 'S':
            print "trade_date=%s: price=%.2f, sell" % (df['trade_date'][i], price)
        if direction == 'B':
            print "trade_date=%s: price = %.2f, buy" % (df['trade_date'][i], price)


test_action("600958.SH")