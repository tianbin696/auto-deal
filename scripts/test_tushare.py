import tushare as ts

token = "546aae3c5aca9eb09c9181e04974ae3cf910ce6c0d8092dde678d1cd"
pro = ts.pro_api(token)

df = ts.pro_bar(pro_api=pro, ts_code='002797.SZ', adj='qfq')
df2 = ts.get_realtime_quotes('002797')

print df2
print df.head()
