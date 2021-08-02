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
        vol = max(100, int(10000/input_price/100)*100)
    return vol


if __name__ == "__main__":
    price = 45.00
    print "buy vol for %.2f: %d" % (price, get_buy_vol(price))

    price = 55.00
    print "buy vol for %.2f: %d" % (price, get_buy_vol(price))

    price = 95.00
    print "buy vol for %.2f: %d" % (price, get_buy_vol(price))

    price = 105.00
    print "buy vol for %.2f: %d" % (price, get_buy_vol(price))

    price = 155.00
    print "buy vol for %.2f: %d" % (price, get_buy_vol(price))

    volume = 100
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 200
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 300
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 400
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 500
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 600
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 700
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 800
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 900
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume))

    volume = 200
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume, 3))

    volume = 200
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume, 101))

    volume = 500
    print "sell vol for %.2f: %d" % (volume, get_sell_vol(volume, 101))
