
------------------------
multip_tools.py 

provides a function 

    run_many_cases_pool(caselist, nprocs, run_one_case, abort_time=5)

that takes a list caselist of dictionaries specifiying parameters needed for
each case, and a function run_one_case that takes a single case dictionary
as input and runs that case.  The Python mulitprocessing.Pool function
is then used to split up the case between nprocs processors.

This module also contains sample code 
    run_one_case_sample(case)
that simply prints out the case number set in case['num'] and 
    make_all_cases_sample()
that creates the caselist.

------------------------
clawmultip_tools.py

This module provides a function that can be used along with multip_tools.py
to easily do a parameter sweep in Clawpack:

    run_one_case_clawpack(case)

    
------------------------
plotclaw.py

Modified version of $CLAW/visclaw/src/python/visclaw/plotclaw.py that allows
passing plotdata in to plotclaw, needed to support parameter sweeps where
setplot might take a case parameter.

