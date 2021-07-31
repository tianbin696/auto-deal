#!/bin/env python
# -*- coding: utf-8 -*-
import logging
from deal_entry import DealEntry

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../../logs/auto_deal_ths.log',
                    filemode='a')
logger = logging.getLogger('deal_loop')


class DealEntries:
    def __init__(self, costs=None, volumes=None):
        self.default_codes = ['002032', '002311', '002271', '600161', '601100', '603899']
        self.codes = self.default_codes
        self.costs = {}
        self.volumes = {}
        if costs:
            for code in costs.keys():
                if code not in self.codes and (code.startswith('0') or code.startswith('6')):
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
    deal_loop.get_deals()