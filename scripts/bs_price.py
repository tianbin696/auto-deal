#!/bin/env python
# -*- coding: utf-8 -*-


def get_buy_price(input_price):
    return input_price * 1.01


def get_sell_price(input_price):
    return input_price * 0.99


if __name__ == "__main__":
    price = 45.00
    print "buy price for %.2f: %.2f" % (price, get_buy_price(price))

    price = 55.00
    print "buy price for %.2f: %.2f" % (price, get_buy_price(price))

    price = 45.00
    print "sell price for %.2f: %.2f" % (price, get_sell_price(price))

    price = 55.00
    print "sell price for %.2f: %.2f" % (price, get_sell_price(price))
