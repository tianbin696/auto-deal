#!/bin/env python
# -*- coding: utf-8 -*-
import time
from deal_entry import DealEntry
from logger_util import logger


class DealEntries:
    def __init__(self, costs=None, volumes=None):
        self.codes = []
        self.costs = {}
        self.volumes = {}
        if costs:
            for code in costs.keys():
                if code not in self.codes:
                    self.codes.append(code)
        for code in list(open("code_candidates.txt")):
            code = code.strip()
            if code not in self.codes:
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
        time.sleep(0.5)
        return __list


if __name__ == "__main__":
    deal_loop = DealEntries()
    print deal_loop.get_deals()

    deal_loop = DealEntries(costs={u'601100': 106.571, u'002271': 51.471, u'600161': 36.443, u'603899': 86.721},
                            volumes={u'601100': 800, u'002271': 1100, u'600161': 2000, u'603899': 700})
    print deal_loop.get_deals()

    print "total count: %d, %s" % (len(deal_loop.codes), deal_loop.codes)
