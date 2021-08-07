#!/bin/env python
# -*- coding: utf-8 -*-
import pandas


def get_h_data_cache(code='600570', end_date='20210101'):
    cache_folder = "resources/cache"
    cache_file = "%s/%s_%s.csv" % (cache_folder, code, end_date)
    return pandas.read_csv(cache_file).reset_index()
