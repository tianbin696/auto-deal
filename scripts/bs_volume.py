#!/bin/env python
# -*- coding: utf-8 -*-


def get_buy_vol(input_price, input_vol=0, max_cost=10000):
    vol = max(100, int(max_cost / (input_price * 100)) * 100)
    if input_vol > 0:
        return min(vol, input_vol)
    return vol


def get_sell_vol(input_vol, input_price=None):
    # sell 1/4 of volume
    vol = max(100, int(input_vol / 400) * 100)
    if input_price:
        if input_vol * input_price < 20000:
            vol = input_vol
        else:
            vol = max(100, int(10000/input_price/100)*100)
            vol = min(input_vol, vol)
    return vol
