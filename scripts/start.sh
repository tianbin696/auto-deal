#!/bin/bash

python auto_deal_THS.py | tee -a ../../logs/auto_deal.log.$(date +"%Y-%m-%d")