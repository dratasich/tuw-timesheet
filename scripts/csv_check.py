#!/usr/bin/env python3

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import string
import sys
import os
import subprocess
import math


#
# config
#

MIN_HOURS_PER_DAY = 8
MAX_HOURS_PER_DAY = 10


#
# argument parsing
#

desc = """Checks the csv timesheet for errors."""

cwd = os.getcwd()

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Input, a csv file.""")
args = parser.parse_args()


#
# read data
#

data = pd.read_csv(args.data, sep=';')

project = list(data)[1]

# replace NaN by 0.0 to be able to calculate with these values
data.loc[data['pHours'].isnull(), 'pHours'] = 0.0
data.loc[data['oHours'].isnull(), 'oHours'] = 0.0
data.loc[data['aHours'].isnull(), 'aHours'] = 0.0

# add overhead column
overhead = data['Total'] - MAX_HOURS_PER_DAY
data.loc[:, 'overhead'] = pd.Series(overhead, index=data.index)
data.loc[data['overhead'] < 0, 'overhead'] = 0.0

# distinguish work day and weekend when checking
weekend = data[data['Date'].str.contains("S")]
work = data[~data['Date'].str.contains("S")]


#
# filter erroneous rows and print
#

def report_error(data, desc="", columns=None):
    if len(data) > 0:
        print("[ERROR] {}:".format(desc))
        if columns is None:
            print(data)
        else:
            print(data[columns])
        print()

error_data = weekend[(weekend['pHours'] > 0)
                     | (weekend['oHours'] > 0)
                     | (weekend['aHours'] > 0)]
report_error(error_data, "hours on weekdays",
             ['Date', 'pHours', 'oHours', 'aHours', 'Total'])

error_data = work[(work['pHours'] > 0) & work[project].isnull()]
report_error(error_data, "description of project too long",
             ['Date', project])

error_data = work[work[project].str.len() > 50]
report_error(error_data, "description of project too long",
             ['Date', project])

error_data = work[(work['pHours'] > 0) & (work['WP'].isnull() | (work['WP'] < 0))]
report_error(error_data, "missing WP", ['Date', 'WP'])

error_data = work[(work['oHours'] > 0) & work['Other Activities'].isnull()]
report_error(error_data, "missing other activities description",
             ['Date', 'Other Activities', 'oHours'])

error_data = work[(work['aHours'] > 0) & work['Absence'].isnull()]
report_error(error_data, "missing absence description",
             ['Date', 'Absence', 'aHours'])

error_data = work[(work['Total'] <= 0) & (work['aHours'] <= 0)]
report_error(error_data, "missing hours",
             ['Date', 'pHours', 'oHours', 'aHours', 'Total'])

error_data = work[work['Total'] != (work['pHours'] + work['oHours'])]
report_error(error_data, "mismatching sum of hours",
             ['Date', 'pHours', 'oHours', 'Total'])

error_data = work[work['Total'] < MIN_HOURS_PER_DAY]
report_error(error_data, "hours per day below minimum",
             ['Date', 'pHours', 'oHours', 'aHours', 'Total'])

error_data = work[work['overhead'] > 0]
report_error(error_data, "too many hours per day",
             ['Date', 'pHours', 'oHours', 'aHours', 'Total', 'overhead'])

overhead = sum(data['overhead'])
if overhead > 0:
    print("total overhead to distribute: {}".format(overhead))

print("Total number or hours: {}".format(sum(data['Total'])))
