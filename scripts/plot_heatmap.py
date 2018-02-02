#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


#
# config
#

desc = """Plots a heatmap of the hours spent per project."""
parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Input for plot, a csv file exported via
                    org-clock-csv from org-agenda-files.""")
parser.add_argument('-p', '--projects', type=str, nargs='+',
                    help="""Projects to plot. The 'parents' column of the
                    org-clock-csv export will be searched.""")
parser.add_argument('-f', '--from', dest='range_from', type=str,
                    help="""Start date.""")
parser.add_argument('-t', '--to', dest='range_to', type=str,
                    help="""End date.""")
parser.add_argument('-e', '--export', type=str,
                    help="Export to file.")
args = parser.parse_args()


#
# read data and plot histogram
#

# read column names (1st line in csv)
with open(args.data, 'r') as f:
    names = f.readline().strip().split(',')
# unfortunately very restricting, error when no str length is given :(
dtype = [(n, 'S100') for n in names]
# load into numpy array
data = np.genfromtxt(args.data, delimiter=',', dtype=dtype,
                     invalid_raise=False, skip_header=1)


#
# data preprocessing
#

# sort w.r.t. start datetime
data.sort(order='start')

def skip(entry):
    # check if entry in range
    if args.range_from and args.range_to:
        s = entry['start'].decode('utf-8') > args.range_from
        e = entry['start'].decode('utf-8') < args.range_to
        if not (s and e):
            return True # skip entry that does not match the date range
    # check if entry in given projects
    if args.projects:
        in_projects = False
        for p in args.projects:
            if p.encode('utf-8') in entry['parents']:
                in_projects = True
        if not in_projects:
            return True # skip entry that does not match any project
    # all checks passed
    return False

# from now on I kick the numpy arrays, because I'm not used to it
clocks = {}
clocks['start'] = []
clocks['end'] = []
clocks['hours'] = []

# make date strings to datetime objects
# calculate hours from start and end clock (ISO)
for i in range(len(data['parents'])):
    if skip(data[i]):
        continue
    start = datetime.strptime(data['start'][i].decode('utf-8'),
                              '%Y-%m-%d %H:%M')
    end = datetime.strptime(data['end'][i].decode('utf-8'),
                            '%Y-%m-%d %H:%M')
    clocks['start'].append(start)
    clocks['end'].append(end)
    clocks['hours'].append((end - start).seconds/3600)

# sum up hours (and create nice shape)
dt0 = clocks['start'][0]
dt1 = clocks['end'][-1]
week0 = int(dt0.strftime('%W'))
week1 = int(dt1.strftime('%W'))
dyear = dt1.year - dt0.year
# shape of efforts map
x = np.arange(week0, dyear*52 + week1 + 2)
y = np.arange(0, 8)
# efforts
bins = np.zeros((len(y), len(x)))
cd = clocks['start'][0].day
cw = week0
cwd = 7 - dt0.weekday()
for i in range(len(clocks['start'])):
    cd = clocks['start'][i].day
    dy = clocks['start'][i].year - dt0.year
    cw = dy*52 + int(clocks['start'][i].strftime('%W'))
    cwd = 7 - clocks['start'][i].weekday()
    bins[cwd-1,cw-week0] += clocks['hours'][i]


#
# plot
#

fig = plt.figure(figsize=(10,2))

colors = [ (0.9, 0.9, 0.9), (0.0, 0.4, 0.6) ]
cm = LinearSegmentedColormap.from_list('efforts', colors, N=10)
plt.pcolormesh(x, y, bins, vmin=0, vmax=8, cmap=cm, edgecolors='w')

plt.title("Efforts Heatmap")
base = dt0.replace(day=1)
month_list = [base + relativedelta(months=m)
              for m in range(dyear*12 + dt1.month - dt0.month + 1)]
xticks = [(dt.year-dt0.year)*52 + int(dt.strftime('%W')) + dt.weekday()/7
          for dt in month_list]
xlabels = [dt.strftime('%Y-%m') if dt.month == 1 else dt.strftime('%m')
           for dt in month_list]
plt.xticks(xticks, xlabels)
plt.yticks([6.5,4.5,2.5], ["Mon", "Wed", "Fri"])

if args.export:
    fig.savefig(args.export)
else:
    plt.show()
