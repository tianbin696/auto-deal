#!/bin/env python
# -*- coding: utf-8 -*-
from scripts.logger_util import logger
from scripts.strategy.intra_day_dual_thrust import IntraDayDualThrust
from scripts.strategy.intra_day_phiary import IntraDayPhiary
from scripts.strategy.intra_day_regression import IntraDayRegression


class IntraDayCompose:
    """
    Test results (code_hs_300):
    - Phiary: 15, Dual Thrust: 15, 0.25, 0.25
        * all: 66.82/0.20
        * filtered: 65.08/0.67
    - Phiary: 20, Dual Thrust: 20, 0.25, 0.25
        * all: 54.08/0.22
        * filtered: 52.26/0.76
    - Phiary: 25, Dual Thrust: 25, 0.25, 0.25
        * all: 45.72/0.24
        * filtered: 44.96/0.81
    - Phiary: 30, Dual Thrust: 30, 0.25, 0.25
        * all: 40.17/0.25
        * filtered: 42.75/0.82
    """
    def __init__(self):
        self.phiary = IntraDayPhiary(days=25)
        self.dual_thrust = IntraDayDualThrust(days=25, k1=0.25, k2=0.25)
        self.regression = IntraDayRegression(self)

    def get_direction(self, rt_df_in, df_h_in):
        direction = self.phiary.get_direction(rt_df_in, df_h_in)
        if direction != "N":
            return direction

        direction = self.dual_thrust.get_direction(rt_df_in, df_h_in)
        if direction == "B":
            # Dual thrust only used for intra day buy
            logger.info("get direction of IntraDualThrust: %s" % direction)
            return direction

        return "N"

    def get_direction_extra(self, rt_df_in, df_h_in):
        direction = self.phiary.get_direction_extra(rt_df_in, df_h_in)
        if direction[0] != "N":
            logger.info("get direction of IntraDayPhiary: %s" % direction[0])
            return direction

        direction = self.dual_thrust.get_direction_extra(rt_df_in, df_h_in)
        if direction[0] == "B":
            # Dual thrust only used for intra day buy
            logger.info("get direction of IntraDayDualThrust: %s" % direction[0])
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
