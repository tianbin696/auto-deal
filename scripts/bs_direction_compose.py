#!/bin/env python
# -*- coding: utf-8 -*-
import scripts.bs_direction_avg as avg
import scripts.bs_direction_rsi as rsi
import scripts.ts_cli as ts
from scripts.logger_util import logger
from scripts.strategy.intra_day_compose import IntraDayCompose
intra = IntraDayCompose()


def get_direction(rt_df_in, df_h_in, is_intra_day_deal):
    rt_price = float(rt_df_in['price'][0])
    if rt_price <= 0:
        return "N"

    if is_intra_day_deal:
        __direction = intra.get_direction(rt_df_in, df_h_in)
        logger.info("direction based on intra: %s" % __direction)
        return __direction

    prices = [rt_price]
    prices.extend(df_h_in['close'])
    __direction = avg.get_direction(prices)
    if __direction == "B" or __direction == "S":
        logger.info("direction based on average: %s" % __direction)
        return __direction

    __direction = rsi.get_direction(prices)
    if __direction == "B" or __direction == "S":
        logger.info("direction based on RSI: %s" % __direction)
    return __direction


def update_cache():
    ts.update_cache()


def update_candidates():
    code_list = intra.update_candidates()
    return code_list


if __name__ == "__main__":
    update_candidates()
