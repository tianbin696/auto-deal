#!/bin/env python
# -*- coding: utf-8 -*-
from deal_entry import DealEntry
from logger_util import logger


class DealEntries:
    def __init__(self, costs=None, volumes=None):
        self.default_codes = ['000100', '000408', '000538', '000568', '000596', '000725',
                              '000895', '000938', '002027', '002294', '002304', '002410',
                              '002456', '002460',
                              '600196', '600219', '600436', '600519', '600660', '600893',
                              '601012', '601828', '601888', '601899', '603156', '603260',
                              '603288', '603799', '603986', '603993']
        self.codes = self.default_codes
        self.costs = {}
        self.volumes = {}
        if costs:
            for code in costs.keys():
                if code not in self.codes and (code.startswith('0') or code.startswith('3') or code.startswith('6')):
                    self.codes.append(code)
        for code in self.codes:
            if costs and code in costs:
                self.costs[code] = costs[code]
            else:
                self.costs[code] = 0.0
            if volumes and code in volumes:
                self.volumes[code] = volumes[code]
            else:
                self.volumes[code] = 0

        self.deal_entries = []
        for code in self.codes:
            self.deal_entries.append(DealEntry(code, self.costs[code], self.volumes[code]))
        logger.info("deal loop initial done for codes: %s" % self.codes)

    def get_deals(self):
        __list = []
        for deal_entry in self.deal_entries:
            deal = deal_entry.get_rt_deal()
            if deal:
                __list.append(deal)
            else:
                logger.info("no deal for code %s" % deal_entry.code)
        logger.info("deals to handle: %s" % __list)
        return __list


if __name__ == "__main__":
    deal_loop = DealEntries()
    print deal_loop.get_deals()

    deal_loop = DealEntries(costs={u'601100': 106.571, u'002271': 51.471, u'600161': 36.443, u'603899': 86.721},
                            volumes={u'601100': 800, u'002271': 1100, u'600161': 2000, u'603899': 700})
    print deal_loop.get_deals()
