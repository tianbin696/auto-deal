#!/bin/env python
# -*- coding: utf-8 -*-
import scripts.ts_cli as ts
from scripts.logger_util import logger
from scripts.strategy.intra_day_compose import IntraDayCompose
from scripts.strategy.intra_day_regression import IntraDayRegression
intra = IntraDayCompose()


def get_direction(rt_df_in, df_h_in, is_intra_day_deal):
    rt_price = float(rt_df_in['price'][0])
    if rt_price <= 0:
        return "N"

    if is_intra_day_deal:
        __direction = intra.get_direction(rt_df_in, df_h_in)
        logger.info("direction based on intra: %s" % __direction)
        return __direction
    return "N"


def update_cache():
    ts.update_cache()


def update_candidates():
    code_list = intra.update_candidates()
    return code_list


if __name__ == "__main__":
    regression = IntraDayRegression(IntraDayCompose())
    regression.get_candidates()
    regression.update_candidates()
