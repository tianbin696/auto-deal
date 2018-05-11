#!/bin/bash

python auto_deal_THS.py | tee -a ../auto_deal.log.$(date +"%Y-%m-%d")