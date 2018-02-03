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

def check(row):
    """Checks row for timesheet requirements. Prints warnings."""
    err = ""
    weekend = True if "Sat" in row[DATE].decode(enc) \
              or "Sun" in row[DATE].decode(enc) else False
    if weekend and (row[PHOURS] > 0 or row[OHOURS] > 0 or row[AHOURS] > 0):
        err += "  [ERROR] hours on a weekend are not allowed\n"
    if (row[PROJECT] is False or row[PROJECT].decode(enc) == "") \
    and row[PHOURS] > 0:
        err += "  [ERROR] missing activity description of project\n"
    if len(row[PROJECT].decode(enc)) > 45:
        err += "  [WARN ] description of project too long\n"
    if row[WP] is False or row[WP] < 0:
        err += "  [ERROR] missing WP\n"
    if (row[OTHER] is False or row[OTHER].decode(enc) == "") \
    and row[OHOURS] > 0:
        err += "  [ERROR] missing other activity\n"
    if (row[ABSENCE] is False or row[ABSENCE].decode(enc) == "") \
    and row[AHOURS] > 0:
        err += "  [ERROR] missing absence description\n"
    # print with date info if errors have occured
    if err != "":
        err = row[DATE].decode(enc) + "\n" + err
        print(err, file=sys.stderr)


#
# print
#

def tex_table_begin():
    header = list(data.dtype.names)
    header[5] = header[7] = header[9] = "Hours"
    align = ['l', '|p{65mm}', 'c', 'c', 'c', 'r', '|p{30mm}', 'r', '|p{30mm}', 'r', '|r']
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
    # format
    weekend = True if "Sat" in row[0].decode(enc) or "Sun" in row[0].decode(enc) else False
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
    # fields
    row[0] = rowcolor + " " + row[0].decode(enc)
    row[1] = row[1].decode(enc)
    row[2] = "{:d}".format(row[2]) if row[2] > 0 else ""  # wp
    row[3] = "{:d}".format(row[3]) if row[3] > 0 else ""  # task
    row[4] = ""
    row[5] = hcellcolor + ("\\texttt{{{:.1f}}}".format(row[5]) if row[5] > 0 else "")
    row[6] = row[6].decode(enc)
    row[7] = hcellcolor + ("\\texttt{{{:.1f}}}".format(row[7]) if row[7] > 0 else "")
    row[8] = row[8].decode(enc)
    row[9] = hcellcolor + ("\\texttt{{{:.1f}}}".format(row[9]) if row[9] > 0 else "")
    row[10] = tcellcolor + "\\texttt{{{:.1f}}}".format(row[10]) if not weekend else ""
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
    for r in data:
        phours_sum += r['pHours']
        ohours_sum += r['oHours']
        ahours_sum += r['aHours']
        # check row and print warnings if any
        check(r)
        # get latex representation
        res += tex_table_clock_row(r)
    res += "\hline"
    res += tex_table_row(["\\textbf{Summary}", "", "", "", "",
                          "\\bf \\texttt{{{:.1f}}}".format(phours_sum), "",
                          "\\bf \\texttt{{{:.1f}}}".format(ohours_sum), "",
                          "\\bf \\texttt{{{:.1f}}}".format(ahours_sum),
                          "\\bf \\texttt{{{:.1f}}}".format(phours_sum+ohours_sum)])
    res += tex_table_end()
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
