from pylab import *
from clawpack.clawutil import runclaw

import os,sys,shutil,pickle

# eventually move the modules needed to $CLAW/clawutil/src/python/clawutil?
#from clawpack.clawutil import multip_tools, clawmultip_tools

# for now use local versions:
CLAW = os.environ['CLAW']
sys.path.insert(0, CLAW + '/clawmultip/src/python/clawmultip')
import multip_tools, clawmultip_tools
sys.path.pop(0)


def make_cases():

    """
    Create a list of the cases to be run, varying a couple rundata parameters
    after setting common parameters from setrun_cases.py.

    The parameters set for each case (as dictionary keys) are determined by
    the fact that we will use clawmultip_tools.run_one_case_clawpack()
    to run a single case.  See that code for more documentation.
    """

    caselist = []

    for mx in [50,100,200]:
        for order in [1,2]:
            case = {}
            outdir = '_output_order%s_mx%s' % (order, str(mx).zfill(4))
            case_name = 'order%s_mx%s' % (order, str(mx).zfill(4))

            case['case_name'] = case_name
            case['outdir'] = outdir
            #case['overwrite'] = False  # NOT WORKING

            #case['xclawcmd'] = None  # if None, will not run code
            case['xclawcmd'] = 'xclaw'  # executable created by 'make .exe'

            # setrun parameters:
            case['setrun_file'] = 'setrun_cases.py'
            setrun_params = {}
            setrun_params['clawdata.order'] = order
            setrun_params['clawdata.num_cells'] = [mx]
            case['setrun_params'] = setrun_params

            #case['plotdir'] = None  # if None, will not make plots
            case['plotdir'] = outdir.replace('_output', '_plots')
            case['setplot_file'] = 'setplot_cases.py'

            # no setplot parameters are set here for this example,
            # instead setplot_cases.setplot has a case argument and uses it
            # to get outdir and case_name used in the title of figures
            setplot_params = {}
            case['setplot_params'] = setplot_params

            # other case-dependent parameters you want to use in setrun
            # or setplot that are not standard attributes of rundata or plotdata
            # (none used this example):
            other_params = {}
            case['other_params'] = other_params

            caselist.append(case)

    return caselist


if __name__ == '__main__':

    # number of Clawpack jobs to run simultaneously:
    nprocs = 4

    caselist = make_cases()

    # run all cases using nprocs processors:
    run_one_case = clawmultip_tools.run_one_case_clawpack
    multip_tools.run_many_cases_pool(caselist, nprocs, run_one_case)
