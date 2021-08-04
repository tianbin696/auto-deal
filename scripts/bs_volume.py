#!/bin/env python
# -*- coding: utf-8 -*-


def get_buy_vol(input_price):
    max_cost = 10000
    vol = max(100, int(max_cost / (input_price * 100)) * 100)
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


if __name__ == "__main__":
    assert get_buy_vol(45.00) == 200
    assert get_buy_vol(55.00) == 100
    assert get_buy_vol(95.00) == 100
    assert get_buy_vol(105.00) == 100
    assert get_sell_vol(100) == 100
    assert get_sell_vol(200) == 100
    assert get_sell_vol(300) == 100
    assert get_sell_vol(400) == 100
    assert get_sell_vol(500) == 100
    assert get_sell_vol(800) == 200
    assert get_sell_vol(900) == 200
    assert get_sell_vol(5000, 3) == 5000
    assert get_sell_vol(7000, 3) == 3300
    assert get_sell_vol(2000, 3) == 2000
    assert get_sell_vol(200, 99) == 200
    assert get_sell_vol(200, 101) == 100
