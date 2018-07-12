#!/usr/bin/env python3

import argparse
import pandas

#
# argument parsing
#

desc = """Outputs hours per WP and task."""

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Timesheet (xslx).""")
args = parser.parse_args()


#
# pandas does everything :)
#

data = pandas.read_excel(args.data, header=2)

# 31 days/rows
data = data.loc[0:30, ['WP', 'Task', 'Hours']]
data = data.fillna(value=0)
print(data.groupby(['WP', 'Task']).sum())
