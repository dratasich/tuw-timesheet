#!/usr/bin/env python3

import argparse
import numpy as np
from datetime import datetime, timedelta


#
# config
#

def valid_month(s):
    try:
        return datetime.strptime(s, "%Y-%m")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

desc = """Prints the effort summary of a month as a table in markdown."""
parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Input for plot, a csv file exported via
                    org-clock-csv from org-agenda-files.""")
parser.add_argument('-m', '--month', type=valid_month,
                    default=datetime.today(),
                    help="""Month in format 'YYYY-MM', e.g.,
                    '2017-07'. Default: last month.""")
parser.add_argument('-p', '--projects', type=str, nargs='+',
                    help="""Projects to plot. The 'parents' column of the
                    org-clock-csv export will be searched.""")
parser.add_argument('-e', '--export', type=str, default='month_summary.md',
                    help="""Export to file.""")
args = parser.parse_args()


#
# read data
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
    # check if entry in month
    dt = datetime.strptime(entry['start'].decode('utf-8'),
                           '%Y-%m-%d %H:%M')
    if dt.year != args.month.year or dt.month != args.month.month:
        return True # skip entry that does not match the month
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
clocks['project'] = []
clocks['start'] = []
clocks['end'] = []
clocks['hours'] = []

# make date strings to datetime objects
# calculate hours from start and end clock (ISO)
for i in range(len(data['start'])):
    if skip(data[i]):
        continue
    start = datetime.strptime(data['start'][i].decode('utf-8'),
                              '%Y-%m-%d %H:%M')
    end = datetime.strptime(data['end'][i].decode('utf-8'),
                            '%Y-%m-%d %H:%M')
    clocks['start'].append(start)
    clocks['end'].append(end)
    clocks['hours'].append((end - start).seconds/3600)
    if data['parents'][i]:
        clocks['project'].append(data['parents'][i].split(b'/', 1)[0])
    else:
        clocks['project'].append(data['task'][i]) # entry that has no parents

# specify which projects to print
if args.projects:
    # use list from arguments (in the given order)
    args.projects = [p.encode('utf-8') for p in args.projects]
else:
    # get the unique headlines
    args.projects = sorted(set(clocks['project']))

# reduce clocks to days
hpd = {}
for p in args.projects:
    hpd[p] = [0] * 31
dt = clocks['start'][0]
for i in range(len(clocks['start'])):
    if clocks['start'][i].day != dt.day:
        dt = clocks['start'][i]
    hpd[clocks['project'][i]][dt.day-1] += clocks['hours'][i]


#
# print
#

# create header
header = list(args.projects)
header.insert(0, b"Date")

with open(args.export, 'w') as f:
    # print header
    f.write("|    Date    |")
    for p in args.projects:
        f.write(" {0:10} |".format(p.decode('utf-8')))
    f.write("\n")
    # print line
    line = "------------------------------" # line template
    f.write("|" + line[0:12] + "|")
    for p in args.projects:
        f.write(line[0:12] + "|")
    f.write("\n")
    # print efforts
    dt = args.month.replace(day=1) # reset to first day of month
    for i in range(len(hpd[args.projects[0]])):
        row = "| " + dt.strftime("%Y-%m-%d") + " |"
        for p in args.projects:
            row += " {0:10.2f} |".format(hpd[p][i])
        f.write(row + "\n")
        dt = dt + timedelta(days=1) # next day
