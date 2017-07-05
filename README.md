org-clock-plot
==============

Plots statistics and timesheets for your boss.

Avoid following characters in the headlines (or you will have to change data
preprocessing in the scripts):
* `,` because it is used as delimiter and causes these lines to
  ignore. Unfortunately numpy cannot parse "column1,text",column2 as two
  columns but interprets it as 3 columns.
* `"` because it is wrapped with another 2 pairs of `"` which would make
  parsing more complicated.


Dependencies
------------

* org-mode (> 8.3)
* [org-clock-csv](https://github.com/atheriel/org-clock-csv) - this great
  extension can be installed via MELPA. Works only with org-mode > 8.3.
* some clock entries in your org-agenda-files ;)
