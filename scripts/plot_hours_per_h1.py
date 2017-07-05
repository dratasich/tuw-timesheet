#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


#
# config
#

desc = """Plots a bar chart of the hours spent per main headline (h1)."""
parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Input for plot, a csv file exported via
                    org-clock-csv from org-agenda-files.""")
parser.add_argument('-f', '--from', dest='range_from', type=str,
                    help="""Start date.""")
parser.add_argument('-t', '--to', dest='range_to', type=str,
                    help="""End date.""")
parser.add_argument('-r', '--resolution', choices=['d','m','y'],
                    help="""Resolution of calculating sums per day ('d'), per
                    month ('m') and per year ('y').""")
parser.add_argument('-p', '--projects', type=str, nargs='+',
                    help="""List of projects to plot. Default: all
                    projects.""")
parser.add_argument('-s', '--stack', action='store_true',
                    help="""Use stack plot.""")
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

# from now on I kick the numpy arrays, because I'm not used to it
clocks = {}
clocks['parents'] = []
clocks['start'] = []
clocks['end'] = []
clocks['hours'] = []

# reduce the 'parents' column to main headline (h1)
# make date strings to datetime objects
# calculate hours from start and end clock (ISO)
for i in range(len(data['parents'])):
    # filter range
    if args.range_from and args.range_to:
        s = data['start'][i].decode('utf-8') > args.range_from
        e = data['start'][i].decode('utf-8') < args.range_to
        if not (s and e):
            continue # skip the lines that do not match
    start = datetime.strptime(data['start'][i].decode('utf-8'),
                              '%Y-%m-%d %H:%M')
    end = datetime.strptime(data['end'][i].decode('utf-8'),
                            '%Y-%m-%d %H:%M')
    clocks['start'].append(start)
    clocks['end'].append(end)
    clocks['parents'].append(data['parents'][i].split(b'/', 1)[0])
    clocks['hours'].append((end - start).seconds/3600)

# specify which projects to print
if args.projects and len(args.projects) > 0:
    # use list from arguments
    clocks['projects'] = [p.encode('utf-8') for p in args.projects]
else:
    # get the unique headlines
    clocks['projects'] = sorted(set(clocks['parents']))

# sum up hours
bins = np.zeros((len(clocks['projects']),1)) # single bin
def add_entry_to(binidx, clki):
    pidx = 0
    try:
        # find project's index
        pidx = clocks['projects'].index(clocks['parents'][clki])
    except ValueError:
        pidx = -1
    if pidx >= 0:
        bins[pidx][binidx] += clocks['hours'][clki]
# sum up hours depending on resolution
if args.resolution == 'd':
    # create bin per day
    bins = np.zeros((len(clocks['projects']),
                     (clocks['end'][-1] - clocks['start'][0]).days))
    curday = clocks['start'][0].day
    curbin = 0
    for i in range(len(clocks['parents'])):
        # next day -> new bin
        if clocks['start'][i].day != curday:
            curday = clocks['start'][i].day
            curbin = curbin + 1
        add_entry_to(curbin, i)
elif args.resolution == 'm':
    # create bin per month
    bins = np.zeros((len(clocks['projects']),
                     round((clocks['end'][-1] - clocks['start'][0]).days/30)))
    curmonth = clocks['start'][0].month
    curbin = 0
    for i in range(len(clocks['parents'])):
        # next month -> new bin
        if clocks['start'][i].month != curmonth:
            curmonth = clocks['start'][i].month
            curbin = curbin + 1
        add_entry_to(curbin, i)
elif args.resolution == 'y':
    # create bin per year
    bins = np.zeros((len(clocks['projects']),
                     round((clocks['end'][-1] - clocks['start'][0]).days/365)+1))
    curyear = clocks['start'][0].year
    curbin = 0
    for i in range(len(clocks['parents'])):
        # next month -> new bin
        if clocks['start'][i].year != curyear:
            curyear = clocks['start'][i].year
            curbin = curbin + 1
        add_entry_to(curbin, i)
else:
    for i in range(len(clocks['parents'])):
        add_entry_to(0, i)


#
# plot
#

fig = plt.figure(figsize=(10,12))

if args.stack:
    labels = [p.decode('utf-8') for p in clocks['projects']]
    plt.stackplot(range(len(bins[0])), bins, baseline='zero', labels=labels)
else:
    for i in range(len(clocks['projects'])):
        plt.plot(bins[i], '-o', label=clocks['projects'][i].decode('utf-8'))

plt.title("Efforts")
plt.xlabel("range")
rotation = 0
if args.resolution == 'd' or args.resolution == 'm':
    xticks = range(len(bins[0]))
    xlabels = []
    for i in range(len(bins[0])):
        dt = clocks['start'][0] + relativedelta(months=i)
        dtstr = dt.strftime("%Y-%m") if dt.month == 1 else dt.strftime("%m")
        xlabels.append(dtstr)
    rotation = 90
elif args.resolution == 'y':
    xticks = range(len(bins[0]))
    xlabels = range(clocks['start'][0].year, clocks['start'][0].year+len(bins[0]))
else:
    xticks = [0]
    xlabels = [""]
plt.xticks(xticks, xlabels, rotation=rotation)
plt.ylabel("hours")
plt.legend()

if args.export:
    fig.savefig(args.export)
else:
    plt.show()
