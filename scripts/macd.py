
import pandas as pd
import numpy as np
import datetime
import time

from tushare_api import TushareAPI
ts = TushareAPI()

def get_EMA(df,N):
    for i in range(len(df)-1, -1, -1):
        if i==len(df)-1:
            df.ix[i,'ema']=df.ix[i,'close']
        if i<len(df)-1:
            df.ix[i,'ema']=(2*df.ix[i,'close']+(N-1)*df.ix[i+1,'ema'])/(N+1)
    ema=list(df['ema'])
    return ema
def get_MACD(df,short=12,long=26,M=9):
    a=get_EMA(df,short)
    b=get_EMA(df,long)
    df['diff']=pd.Series(a)-pd.Series(b)
    #print(df['diff'])
    for i in range(len(df)-1, -1, -1):
        if i==len(df)-1:
            df.ix[i,'dea']=df.ix[i,'diff']
        if i<len(df)-1:
            df.ix[i,'dea']=(2*df.ix[i,'diff']+(M-1)*df.ix[i+1,'dea'])/(M+1)
    df['macd']=2*(df['diff']-df['dea'])
    return df

# df = ts.get_h_data("000789", None, 0)
# get_MACD(df,12,26,9)
# print(df)
