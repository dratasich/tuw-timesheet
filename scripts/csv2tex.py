#!/usr/bin/env python3

import argparse
import numpy as np
from datetime import datetime, timedelta
import string
import sys
import os
import subprocess


#
# config
#

MIN_HOURS_PER_DAY = 8
MAX_HOURS_PER_DAY = 10


#
# argument parsing
#

desc = """Generates the monthly TUW timesheet from a csv."""

cwd = os.getcwd()

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('data', type=str,
                    help="""Input, a csv file.""")
parser.add_argument('-t', '--template', type=argparse.FileType('r'),
                    default="{}/templates/timesheet.tex".format(cwd),
                    help="""Latex template file. The variable $efforts will be
                    replaced by the efforts table.""")
parser.add_argument('-n', '--name', default="TBD",
                    help="""Your name.""")
args = parser.parse_args()


#
# read data
#

enc = 'utf-8'

# load into numpy array
data = np.genfromtxt(args.data, delimiter=';', dtype=None, names=True,
                     invalid_raise=False)

# field indices
field_idx = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
DATE, PROJECT, WP, TASK, ACT, PHOURS, OTHER, OHOURS, ABSENCE, AHOURS, TOTAL = field_idx
assert len(field_idx) == len(data[0]), "column number mismatch"


# load template
template = string.Template(args.template.read())


#
# check row
#


def check_weekday(row, err="", overhead=0):
    """Appends errors concerning weekday."""
    if (row[PROJECT] is False or row[PROJECT].decode(enc) == "") \
       and row[PHOURS] > 0:
        err += "  [ERROR] missing activity description of project\n"
    if len(row[PROJECT].decode(enc)) > 50:
        err += "  [WARN ] description of project too long\n"
    if (row[WP] is False or row[WP] < 0) and row[PHOURS] > 0:
        err += "  [ERROR] missing WP\n"
    if (row[OTHER] is False or row[OTHER].decode(enc) == "") \
       and row[OHOURS] > 0:
        err += "  [ERROR] missing other activity\n"
    if (row[ABSENCE] is False or row[ABSENCE].decode(enc) == "") \
       and row[AHOURS] > 0:
        err += "  [ERROR] missing absence description\n"
    if row[TOTAL] == 0 and row[AHOURS] == 0:
        err += "  [ERROR] missing clocks for this day\n"
    if row[TOTAL] != (row[PHOURS] + row[OHOURS]):
        err += "  [ERROR] total of hours mismatch (total != phours + ohours)\n"
    if row[TOTAL] > 0 and row[TOTAL] < MIN_HOURS_PER_DAY:
        err += "  [ERROR] hours per day below minimum\n"
    if row[TOTAL] > MAX_HOURS_PER_DAY:
        overhead += row[TOTAL] - MAX_HOURS_PER_DAY
        err += "  [ERROR] exceeds max hours per day ({:.1f}h)\n".format(overhead)
    return err, overhead

def check_weekend(row, err="", overhead=0):
    """Appends errors concerning weekend."""
    if row[PHOURS] > 0 or row[OHOURS] > 0 or row[AHOURS] > 0:
        overhead += row[TOTAL]
        err += "  [ERROR] hours on a weekend are not allowed ({:.1f})\n".format(overhead)
    return err, overhead

def check(row):
    """Checks row for timesheet requirements.

    Prints warnings. Returns the amount of hours that exceed 10h per day (hours
    that shall be re-assigned to other days).

    """
    err = ""
    overhead = 0
    weekend = True if "Sat" in row[DATE].decode(enc) \
              or "Sun" in row[DATE].decode(enc) else False
    if weekend:
        err, overhead = check_weekend(row)
    else:
        err, overhead = check_weekday(row)
    # print with date info if errors have occured
    if err != "":
        err = row[DATE].decode(enc) + "\n" + err
        print(err, file=sys.stderr)
    # return the overhead over the maximum allowed hours per day
    return overhead


#
# print
#

def tex_table_begin():
    header = list(data.dtype.names)
    header[PHOURS] = header[OHOURS] = header[AHOURS] = "Hours"
    align = ['l', '|p{70mm}', 'c', 'c', 'c', 'r', '|p{30mm}', 'r', '|p{30mm}',
             'r', '|r']
    if len(header) != len(align):
        RuntimeError("column number mismatch")
    # format
    header = map(lambda h: "\\textbf{" + h.replace("_", " ") + "}", header)
    # latex
    res = """
    \\begin{{tabular}}{{|{spec}|}}
    \hline
    {header} \\\\ \hline \hline
    """.format(spec="|".join(align), header=" & ".join(header))
    return res

def tex_table_end():
    res = """
    \\end{tabular}
    """
    return res

def tex_table_row(row):
    res = " & ".join(row) + "\\\\ \hline"
    return res

def tex_table_clock_row(row):
    row = list(row)
    weekend = True if "Sat" in row[DATE].decode(enc) \
              or "Sun" in row[0].decode(enc) else False
    # colors
    rowcolor = ""
    if weekend:
        rowcolor = "\\rowcolor{lightgray}\n    "
    else:
        rowcolor = "\\rowcolor{\\tuwBlue!5!white}\n    "
    tcellcolor = ""
    if not weekend:
        if row[10] < 8:
            tcellcolor = "\\cellcolor{red!30!white} "
        else:
            tcellcolor = "\\cellcolor{\\tuwBlue!40!white} "
    hcellcolor = ""
    if not weekend:
        hcellcolor = "\\cellcolor{\\tuwBlue!20!white} "
    # format fields
    row[DATE] = rowcolor + " " + row[0].decode(enc)
    row[PROJECT] = row[1].decode(enc)
    row[WP] = "{:d}".format(row[2]) if row[2] > 0 else ""
    row[TASK] = "{:d}".format(row[3]) if row[3] > 0 else ""
    row[ACT] = ""
    row[PHOURS] = hcellcolor + ("\\texttt{{{:.1f}}}".format(row[5])
                                if row[5] > 0 else "")
    row[OTHER] = row[6].decode(enc)
    row[OHOURS] = hcellcolor + ("\\texttt{{{:.1f}}}".format(row[7])
                                if row[7] > 0 else "")
    row[ABSENCE] = row[8].decode(enc)
    row[AHOURS] = hcellcolor + ("\\texttt{{{:.1f}}}".format(row[9])
                                if row[9] > 0 else "")
    row[TOTAL] = tcellcolor + "\\texttt{{{:.1f}}}".format(row[10]) \
                 if not weekend else ""
    # latex
    res = tex_table_row(row)
    return res

def tex_efforts():
    res = ""
    res += tex_table_begin()
    # print efforts in a table
    phours_sum = 0
    ohours_sum = 0
    ahours_sum = 0
    overhead = 0
    for r in data:
        phours_sum += r['pHours']
        ohours_sum += r['oHours']
        ahours_sum += r['aHours']
        # check row and print warnings if any
        overhead += check(r)
        # get latex representation
        res += tex_table_clock_row(r)
    res += "\hline"
    res += tex_table_row(["\\textbf{Summary}", "", "", "", "",
                          "\\bf \\texttt{{{:.1f}}}".format(phours_sum), "",
                          "\\bf \\texttt{{{:.1f}}}".format(ohours_sum), "",
                          "\\bf \\texttt{{{:.1f}}}".format(ahours_sum),
                          "\\bf \\texttt{{{:.1f}}}".format(phours_sum+ohours_sum)])
    res += tex_table_end()
    if overhead > 0:
        print("\nTotal overhead to distribute: {:.1f}".format(overhead),
              file=sys.stderr)
    return res


#
# output
#

# write tex (temp file)
with open(args.data.replace(".csv", ".tex"), 'w') as f:
    s = template.substitute({
        'name': args.name,
        'efforts': tex_efforts()
    })
    f.write(s)
    f.close()
