#!/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

import pytz


def format_date(num):
    if num < 10:
        return "0%d" % num
    else:
        return "%d" % num


def compare_time(hour, minute):
    tz = pytz.timezone('Hongkong')
    now = datetime.now(tz)
    target_str = "%d-%s-%s %s:%s:00" % (now.year, format_date(now.month), format_date(now.day), hour, minute)
    target_time = tz.localize(datetime.strptime(target_str, "%Y-%m-%d %H:%M:%S"))
    return now > target_time


if __name__ == "__main__":
    res = compare_time("09", "25")
    print("now is after 09:25: %s" % res)

    res = compare_time("15", "05")
    print("now is after 15：05: %s" % res)
