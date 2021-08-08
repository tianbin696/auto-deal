#!/bin/env python 
import unittest
from scripts.bs_volume import get_buy_vol, get_sell_vol


class BsVolumeTest(unittest.TestCase):
    def test_buy_vol(self):
        self.assertEqual(get_buy_vol(45.00), 200)
        self.assertEqual(get_buy_vol(55.00), 100)
        self.assertEqual(get_buy_vol(95.00), 100)
        self.assertEqual(get_buy_vol(105.00), 100)
    
    def test_sell_vol(self):
        self.assertEqual(get_sell_vol(100), 100)
        self.assertEqual(get_sell_vol(200), 100)
        self.assertEqual(get_sell_vol(300), 100)
        self.assertEqual(get_sell_vol(400), 100)
        self.assertEqual(get_sell_vol(500), 100)
        self.assertEqual(get_sell_vol(800), 200)
        self.assertEqual(get_sell_vol(900), 200)
        self.assertEqual(get_sell_vol(5000, 3), 5000)
        self.assertEqual(get_sell_vol(7000, 3), 3300)
        self.assertEqual(get_sell_vol(2000, 3), 2000)
        self.assertEqual(get_sell_vol(200, 99), 200)
        self.assertEqual(get_sell_vol(200, 101), 100)
