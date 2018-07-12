#!/usr/bin/env python3

import argparse
import pandas as pd

#
# argument parsing
#

desc = """Outputs hours per WP and task."""

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Timesheet (xslx).""")
parser.add_argument('--skip', type=int, default=2,
                    help="""Lines to skip. Line number of the columns head
                    (including WP, Task, Hours) minus 1.""")
parser.add_argument('--header', type=str,
                    help="""Header in CSV format (delimiter ',') for the
                    summary output, e.g., "2,4.1" will print the summary for
                    WP2 and WP4 Task1. Separate WP from tasks with '.'.""")
args = parser.parse_args()


#
# pandas does everything :)
#

data = pd.read_excel(args.data, header=args.skip)

# 31 days/rows
data = data.loc[0:30, ['WP', 'Task', 'Hours']]
# fill missing values (NaN) with zeros
data = data.fillna(value=0)
# remove zero hours lines
data = data[data.Hours > 0]
# convert WP and task to int
data[['WP', 'Task']] = data[['WP', 'Task']].astype(int)

#  wp and task w.r.t. given header
header = []
if args.header is not None:
    cols = args.header.split(',')
    for c in cols:
        parts = c.split('.')
        wp = 0
        task = 0
        try:
            wp = int(parts[0])
            task = int(parts[1])
        except:
            pass
        header.append((wp, task))
        df = pd.DataFrame([[wp, task, 0]], columns=list(data.columns))
        data = data.append(df)

gb = data.groupby(['WP', 'Task'])

if args.header is None:
    # print generic summary (histogram)
    print(gb.sum())
else:
    # print summary according to header
    hours = [data.loc[gb.groups[h], 'Hours'].sum() for h in header]
    hours = [str(h) if h > 0 else "" for h in hours]
    head = [str(wp) + '.' + str(task) for wp, task in header]
    print('\t'.join(head))
    print('\t'.join(hours))
