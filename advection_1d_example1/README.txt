
Modified example from $CLAW/classic/examples/advection_1d_example1

The code in run_cases_clawpack.py runs 6 different cases:
    3 resolutions mx = 50, 100, 200 points
    each with order = 1 and order = 2

Run this script via:

    $ python run_cases_clawpack.py

and 6 output and plots directories should be created.  To view all the
plots in 6 separate browser tabs, open _plots*/allframes_fig1.html

The run_cases_clawpack.py creates a caselist of dictionaries for the 
cases to be run.

setrun_cases.py contains the setrun function, with an additional parameter case
so that a single case dictionary can be passed in for use in setting up
a single run.

Similarly, setplot_cases.py provides the setplot function, with an
additional parameter case so that the titles of the plots can be properly
formed for each particular case.


Code from $CLAW/clawmultip/src/python/clawmultip is used, see the README.txt
file in that directory for more information.

