#!/bin/env python
import unittest
from scripts.bs_price import get_buy_price, get_sell_price


class BsPriceTest(unittest.TestCase):
    def test_buy_price_1(self):
        self.assertEqual(get_buy_price(45.00), 45.45)

    def test_sell_price_1(self):
        self.assertEqual(get_sell_price(45.00), 44.55)
