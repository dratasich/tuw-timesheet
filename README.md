Timesheets
==========

Plots statistics and timesheets for your boss.


Usage
--------------------------

Export the org-mode clocks to a csv.

```
(emacs) M-x org-clock-csv
(emacs) C-x C-w
        Write file: <path>/clock.csv
```

### Monthly Timesheet

See the usage of the scripts with the option `-h`.

Example:

```bash
$ ./scripts/org2csv.py -m 2018-01 -p IoT4CPS data/clocks.csv
$ ./scripts/csv2tex.py --template=templates/timesheet.tex data/2018-01.csv
$ pdflatex 2018-01.tex
```

`csv2tex` will print warnings and errors considering some timesheet
requirements (e.g., working hours <= 10 per day). Change the csv where needed
and re-run `csv2tex`.

Avoid following characters in the headlines of your org-file (or you will have
to change data preprocessing in the scripts):
* `,` because it is used as delimiter and causes these lines to
  ignore. Unfortunately numpy cannot parse "column1,text",column2 as two
  columns but interprets it as 3 columns.
* `"` because it is wrapped with another 2 pairs of `"` which would make
  parsing more complicated.
* German Umlaute because of the encoding.

If you only want to check the csv, use:
```bash
$ ./scripts/csv_check.py 2018-01.csv
```

### Heatmap

```bash
$ ./scripts/plot_heatmap.py data/clocks.csv -p IoT4CPS -f 2018-01
```


Dependencies
------------

### templates/timesheet.tex

The timesheet latex template includes the TU Wien logo. Remove or download from
the
[official website](https://www.tuwien.ac.at/en/services/public_relations_office/publishing_web_print/corporate_design/tu_logo/).

### org2csv

* [org-mode](http://orgmode.org/) (> 8.3)
* [org-clock-csv](https://github.com/atheriel/org-clock-csv) exports the clock
  entries of an org-file to csv. This great extension can be installed via
  [MELPA](https://melpa.org/#/getting-started). Works only with org-mode > 8.3.
* some clock entries in your org-agenda-files ;)
