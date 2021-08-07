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
        self.regression = IntraDayRegression(self)

    def get_direction(self, rt_df_in, df_h_in):
        direction = self.phiary.get_direction(rt_df_in, df_h_in)
        if direction != "N":
            return direction

        direction = self.dual_thrust.get_direction(rt_df_in, df_h_in)
        if direction != "N":
            logger.info("get direction of IntraDualThrust: %s" % direction)
            return direction

        return "N"

    def get_direction_extra(self, rt_df_in, df_h_in):
        direction = self.phiary.get_direction_extra(rt_df_in, df_h_in)
        if direction[0] != "N":
            logger.info("get direction of IntraDayPhiary: %s" % direction[0])
            return direction

        direction = self.dual_thrust.get_direction_extra(rt_df_in, df_h_in)
        if direction[0] != "N":
            logger.info("get direction of IntraDualThrust: %s" % direction[0])
            return direction

        return "N"

    def get_candidates(self):
        return self.regression.get_candidates()

    def update_candidates(self):
        self.regression.get_candidates()
        self.regression.update_candidates()
        return self.regression.final_list


if __name__ == "__main__":
    regression = IntraDayRegression(IntraDayCompose())
    regression.get_candidates()
    regression.update_candidates()
