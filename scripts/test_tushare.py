import tushare as ts
import numpy
from macd import get_MACD
from auto_deal_THS import get_direction_by_rsi
from auto_deal_THS import getRSI

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)


def test_api():
    df = ts.pro_bar(pro_api=pro, ts_code='002797.SZ', adj='qfq')
    df2 = ts.get_realtime_quotes('002797')

    print df2
    print df.head()


def test_action(code):
    df = ts.pro_bar(pro_api=pro, ts_code=code, adj="qfq")
    result = []
    result.append("%s:RSI:%.2f" % (df['trade_date'][0], getRSI(df['close'], 24)))
    for i in range(120):
        price = df['close'][i]
        direction = get_direction_by_rsi(code, df['close'][i:], 24, False)

        if direction == 'S':
            print "code=%s, trade_date=%s: price=%.2f, sell" % (code, df['trade_date'][i], price)
            result.append("S:%s:%.2f" % (df['trade_date'][i], price))
        if direction == 'B':
            print "code=%s, trade_date=%s: price = %.2f, buy" % (code, df['trade_date'][i], price)
            result.append("B:%s:%.2f" % (df['trade_date'][i], price))
    return result


def test():
    result = {}
    for code in list(open("../codes/candidates.txt")):
        code = code.strip()
        if int(code) < 600000:
            code_str = "%s.SZ" % code
        else:
            code_str = "%s.SH" % code
        result[code] = test_action(code_str)

    for code in result.keys():
        print "code=%s, result=%s" % (code, result[code])


test()
