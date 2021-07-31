import tushare as ts
from backup.auto_deal_THS import get_direction_by_rsi
from backup.auto_deal_THS import getRSI

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)
cache = {}


def test_api():
    df = ts.pro_bar(pro_api=pro, ts_code='002797.SZ', adj='qfq')
    df2 = ts.get_realtime_quotes('002797')

    print df2
    print df.head()


def test_action(code, is_logging=False):
    df = ts.pro_bar(pro_api=pro, ts_code=code, adj="qfq")
    cache[code] = df
    result = []
    result.append("%s:RSI:%.2f" % (df['trade_date'][0], getRSI(df['close'], 24)))
    for i in range(120):
        price = df['close'][i]
        rsi = getRSI(df['close'][i:], 24)
        rsi_1 = getRSI(df['close'][i+1:], 24)
        direction = get_direction_by_rsi(code, df['close'][i:], 24, is_logging)

        if direction == 'S':
            print "code=%s, trade_date=%s: price=%.2f, rsi=%.2f, rsi_1=%.2f, sell" % (code, df['trade_date'][i], price, rsi, rsi_1)
            result.append("S:%s:%.2f" % (df['trade_date'][i], price))
        if direction == 'B':
            print "code=%s, trade_date=%s: price=%.2f, rsi=%.2f, rsi_1=%.2f, buy" % (code, df['trade_date'][i], price, rsi, rsi_1)
            result.append("B:%s:%.2f" % (df['trade_date'][i], price))
    return result


def sort_by_rsi(codes, days_ago=0):
    rsis = []
    for code in codes:
        rsis.append(getRSI(cache[code]['close'][days_ago:], 24))
    rsis.sort()
    print "RSIs=%s" % rsis


def test():
    result = {}
    code_strs = []
    for code in list(open("../codes/candidates.txt")):
        code = code.strip()
        if int(code) < 600000:
            code_str = "%s.SZ" % code
        else:
            code_str = "%s.SH" % code
        code_strs.append(code_str)
        result[code] = test_action(code_str)

    for code in result.keys():
        print "code=%s, result=%s" % (code, result[code])

    for i in range(2, -1, -1):
        sort_by_rsi(code_strs, i)

    for code in result.keys():
        rsi = float(result[code][0].split(":")[2])
        if 50 < rsi < 55:
            print "code=%s, result:%s" % (code, result[code])


test()
