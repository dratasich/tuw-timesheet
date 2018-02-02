#!/usr/bin/env python3

import argparse
import numpy as np
from datetime import datetime, timedelta


#
# config
#

desc = """Generates the monthly TUW timesheet as csv from an org-mode csv.

The effort summary of a month is printed to a csv. All parents (except the
given project, 'Lunch' and 'Absence') are used directly as description of
'Other Activities'.

Example org-file:
* ProjectName
* Research
* Teaching
* Training
* Administration
* Absence
* Lunch
"""

def valid_month(s):
    try:
        return datetime.strptime(s, "%Y-%m")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Input, a csv file exported via org-clock-csv from
                    org-agenda-files.""")
parser.add_argument('-m', '--month', type=valid_month,
                    default=datetime.today(),
                    help="""Month in format 'YYYY-MM', e.g.,
                    '2017-07'. Default: last month.""")
parser.add_argument('-p', '--project', type=str, required=True,
                    help="""Project for which the timesheet shall be
                    generated. All other hours will be summed up. Only the
                    description matching the project will be extracted.""")
args = parser.parse_args()


#
# read data
#

enc = 'utf-8'

# load into numpy array
data = np.genfromtxt(args.data, delimiter=',', dtype=None, names=True,
                     invalid_raise=False)


#
# data preprocessing
#

# sort w.r.t. start datetime
data.sort(order='start')

def skip(entry):
    # check if entry in month
    dt = datetime.strptime(entry['start'].decode(enc),
                           '%Y-%m-%d %H:%M')
    if dt.year != args.month.year or dt.month != args.month.month:
        return True # skip entry that does not match the month
    # all checks passed
    return False

# from now on I kick the numpy arrays, because I'm not used to it
clocks = {}
clocks['project'] = []
clocks['parents'] = []
clocks['start'] = []
clocks['end'] = []
clocks['hours'] = []
clocks['desc'] = []

# make date strings to datetime objects
# calculate hours from start and end clock (ISO)
for i in range(len(data['start'])):
    if skip(data[i]):
        continue
    start = datetime.strptime(data['start'][i].decode(enc),
                              '%Y-%m-%d %H:%M')
    end = datetime.strptime(data['end'][i].decode(enc),
                            '%Y-%m-%d %H:%M')
    clocks['start'].append(start)
    clocks['end'].append(end)
    clocks['hours'].append((end - start).seconds/3600)
    if data['parents'][i]:
        clocks['project'].append(data['parents'][i].split(b'/', 1)[0])
    else:
        clocks['project'].append(data['task'][i]) # entry that has no parents
    clocks['parents'].append(data['parents'][i]) # save all parents
    clocks['desc'].append(data['task'][i]) # save description

topics = sorted(set(clocks['project']))

# reduce clocks and description to days
hpd = {}  # hours per day
dpd = {}  # all topics description per day
ppd = {}  # parents per day
# each topic gets a hpd, dpd, ppd
for t in topics:
    hpd[t] = [0] * 31
    dpd[t] = [None] * 31
    ppd[t] = [None] * 31
# collect to days
dt = clocks['start'][0]
for i in range(len(clocks['start'])):
    if clocks['start'][i].day != dt.day:
        dt = clocks['start'][i]
    hpd[clocks['project'][i]][dt.day-1] += clocks['hours'][i]
    # create list for descriptions of the day
    if dpd[clocks['project'][i]][dt.day-1] is None:
        dpd[clocks['project'][i]][dt.day-1] = list()
    dpd[clocks['project'][i]][dt.day-1].append(clocks['desc'][i].decode(enc))
    # create list of parents per day
    if ppd[clocks['project'][i]][dt.day-1] is None:
        ppd[clocks['project'][i]][dt.day-1] = list()
    ppd[clocks['project'][i]][dt.day-1].append(clocks['parents'][i].decode(enc))


def cat_description(date, project):
    # concatinate information to a single search string
    searchstr = ""
    if dpd[project][date.day-1] is not None:
        searchstr += ",".join(dpd[project][date.day-1])
    searchstr += ","
    if ppd[project][date.day-1] is not None:
        searchstr += ",".join(ppd[project][date.day-1])
    return searchstr

# round up to 1/2h project (round down other)
def clocks_phours(date, project, topics):
    hours = hpd[project][date.day-1]
    # search lunch in topics
    had_lunch = False
    for t in topics:
        searchstr = cat_description(date, t)
        if "Lunch" in searchstr or "lunch" in searchstr:
            had_lunch = True
    if had_lunch:
        hours += 0.5
    # round
    hours = round(hours*2)/2
    return hours

def clocks_other(date, project, topics):
    # defaults
    ohours = 0
    ohours_max = 0
    otopic_max = ""
    ahours = 0
    atopic = ""
    # sum up the hours of the topics
    for t in topics:
        # ignore the project
        if project == t:
            continue
        if "Absence" in t.decode(enc):
            # handle absence
            try:
                atopic = dpd[t][date.day-1][0]
            except:
                atopic = ""
            ahours += hpd[t][date.day-1]
        else:
            # handle other
            ohours += hpd[t][date.day-1]
            if hpd[t][date.day-1] > ohours_max:
                ohours_max = hpd[t][date.day-1]
                otopic_max = t.decode(enc)
    # round
    ohours = round(ohours*2)/2
    ahours = round(ahours*2)/2
    return otopic_max, ohours, atopic, ahours

# extract project work packages
def clocks_wp(date, project):
    # default
    wp = -1
    task = -1
    # search 'WP'
    searchstr = cat_description(date, project)
    if 'WP' in searchstr:
        i = searchstr.index('WP')
        try:
            wp = int(searchstr[i+2:i+3])
            if searchstr[i+3] == '.':
                task = int(searchstr[i+4:i+5])
        except:
            pass
    return wp, task


#
# print
#

def csv_begin():
    header = ["Date", args.project, "WP", "Task", "ACT", "pHours",
              "Other Activities", "oHours", "Absence", "aHours",
              "Total"]
    # csv
    res = "#" + ";".join(header) + "\n"
    return res

def csv_end():
    res = ""
    return res

def csv_row(row):
    res = ";".join(row) + "\n"
    return res

def csv_clock_row(date, desc, wp, task=-1, act="", phours=8, other="", ohours=0,
                  absence="", ahours=0, total=8):
    row = [
        "{:%Y-%m-%d %a}".format(date),
        desc,
        "{:d}".format(wp),
        "{:d}".format(task),
        act,
        "{:.1f}".format(phours),
        other,
        "{:.1f}".format(ohours),
        absence,
        "{:.1f}".format(ahours),
        "{:.1f}".format(total)
    ]
    res = csv_row(row)
    return res

def csv_efforts():
    res = ""
    res += csv_begin()
    # print efforts (a table row for each day)
    dt = args.month.replace(day=1)  # reset to first day of month
    project = args.project.encode(enc)
    for i in range(len(hpd[topics[0]])):
        # hours
        phours = clocks_phours(dt, project, topics)
        # get WP and task
        wp, task = clocks_wp(dt, project)
        # description for project activity
        desc = ""
        if dpd[project][i] is not None:
            desc = ", ".join(set(dpd[project][i]))
        # other columns
        otopic, ohours, atopic, ahours = clocks_other(dt, project, topics)
        # get latex representation
        res += csv_clock_row(
            date=dt,
            desc=desc,
            wp=wp,
            task=task,
            phours=phours,
            other=otopic,
            ohours=ohours,
            absence=atopic,
            ahours=ahours,
            total=phours + ohours
        )
        dt = dt + timedelta(days=1)  # next day
    res += csv_end()
    return res


#
# output
#

with open("{:%Y-%m}.csv".format(args.month), 'w') as f:
    s = csv_efforts()
    f.write(s)
    f.close()
