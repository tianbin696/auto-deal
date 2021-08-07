#!/bin/env python
# -*- coding: utf-8 -*-
from scripts.logger_util import logger
from scripts.strategy.intra_day_dual_thrust import IntraDayDualThrust
from scripts.strategy.intra_day_phiary import IntraDayPhiary
from scripts.strategy.intra_day_regression import IntraDayRegression


class IntraDayCompose:
    def __init__(self):
        self.phiary = IntraDayPhiary()
        self.dual_thrust = IntraDayDualThrust()

    def get_direction(self, rt_df_in, df_h_in):
        __direction = self.phiary.get_direction(rt_df_in, df_h_in)
        if __direction != "N":
            return __direction
        return "N"

    def get_direction_extra(self, rt_df_in, df_h_in):
        direction = self.phiary.get_direction_extra(rt_df_in, df_h_in)
        if direction[0] != "N":
            logger.info("get direction of IntraDayPhiary: %s" % direction[0])
            return direction

        # direction = self.dual_thrust.get_direction_extra(rt_df_in, df_h_in)
        # if direction[0] != "N":
        #     logger.info("get direction of IntraDualThrust: %s" % direction[0])
        #     return direction

        return "N"

    def update_candidates(self):
        __regression = IntraDayRegression(self)
        __regression.get_candidates()
        __regression.update_candidates()
        return __regression.final_list


if __name__ == "__main__":
    strategy = IntraDayCompose()
    regression = IntraDayRegression(strategy)
    regression.get_candidates()
    regression.update_candidates()
