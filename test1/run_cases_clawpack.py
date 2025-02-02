from pylab import *
from clawpack.clawutil import runclaw

import sys
import multip_tools
import multiprocessing
from multiprocessing import Process, current_process
import os,sys,shutil,pickle
import numpy
#import util
import logging
import contextlib


def set_rundata_params(rundata, setrun_params):
    """
    Set
        rundata.<key> = <value>
    for each key in the dictionary setrun_params.
    Move to multip_tools module eventually.
    """
    keys = setrun_params.keys()
    for key in keys:
        value = setrun_params[key]
        setcmd = 'rundata.%s = %s' % (key, value)
        try:
            exec(setcmd)
            print('Reset: %s' % setcmd)
        except:
            print('Command failed: %s' % setcmd)
            raise

    return rundata


xclawcmd = 'xclaw'
run_clawpack = True
make_plots = False

runs_dir = os.path.abspath('.')

def run_one_case(case):
    """
    Input *case* should be a dictionary with any parameters needed to set up
    and run a specific case.

    It is assumed that all values in setrun.py will be
    used for every run with the exception of the parameters set for each case.
    """

    import datetime
    from clawpack.clawutil.runclaw import runclaw
    from clawpack.visclaw.plotclaw import plotclaw
    from setrun_cases import setrun

    p = current_process()

    # unpack the dictionary:

    outdir = case['outdir']
    plotdir = case.get('plotdir', None)
    case_name = case['case_name']
    setrun_params = case.get('setrun_params', {}) # setrun params to change
    params = case.get('params', {})  # dictionary for any other case parameters


    if not os.path.isdir(outdir):
        try:
            os.mkdir(outdir)
            print('Created %s' % outdir)
        except:
            raise Exception("Could not create directory: %s" % outdir)


    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    message = "Process %i started   case %s at %s\n" \
                % (p.pid, case_name, timenow)

    fname_log = os.path.join(outdir, 'python_log.txt')
    print("Python output from this run will go to\n   %s\n" \
                        % fname_log)

    #logging.basicConfig(filename=fname_log,level=logging.INFO)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.info(message)

    # initialize rundata using setrun but then change some things for each run:
    rundata = setrun()

    rundata = set_rundata_params(rundata, case['setrun_params'])

    # write .data files in outdir:
    rundata.write(outdir)

    stdout_fname = outdir + '/python_output.txt'
    try:
        stdout_file = open(stdout_fname, 'w')
        message = message +  "Python output from this run will go to\n   %s\n" \
                            % stdout_fname
    except:
        print(message)
        raise Exception("Cannot open file %s" % stdout_fname)

    message = message +  "Fortran output from this run will go to\n   %s\n" \
                        % (outdir+'/nohup.out')

    print(message)

    # Redirect stdout,stderr so any print statements go to a unique file...
    import sys
    sys_stdout = sys.stdout
    sys.stdout = stdout_file
    sys_stderr = sys.stderr
    sys.stderr = stdout_file

    # write out all case parameters:
    fname = os.path.join(outdir, 'case_info.txt')
    with open(fname,'w') as f:
        f.write('case %s\n' % case['case_name'])
        for k in case.keys():
            f.write('%s:  %s\n' % (k.ljust(20), case[k]))
        if 0:
            f.write('-----------\nsetrun_params:\n')
            setrun_params = case['setrun_params']
            for k in setrun_params.keys():
                f.write('%s:  %s\n' % (k.ljust(20), setrun_params[k]))
    print('Created %s' % fname)

    # pickle case dictionary for reloading later:
    fname = os.path.join(outdir, 'case_info.pkl')
    with open(fname, 'wb') as f:
        pickle.dump(case, f)
    print('Created %s' % fname)

    # global summary file:
    fname = 'case_summary.txt'
    with open(fname,'a') as f:
        f.write('=========\ncase %s\n' % case['case_name'])
        for k in case.keys():
            f.write('%s:  %s\n' % (k.ljust(20), case[k]))

    if run_clawpack:
        # Run the clawpack executable
        if not os.path.isfile(xclawcmd):
            raise Exception('Executable %s not found' % xclawcmd)

        # Use data from rundir=outdir, which was just written above...
        runclaw(xclawcmd=xclawcmd, outdir=outdir,
                rundir=outdir, nohup=True)

    stdout_file.close()
    # Fix stdout again
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    message = "Process %i completed case %s at %s\n" \
                % (p.pid, case_name, timenow)
    print(message)
    logger.info(message)


def make_cases():

    """
    Create a list of the cases to be run.
    """

    caselist = []
    for mx in [100,200]:
        for order in [1,2]:
            case = {}
            outdir = 'order%s_mx%s' % (order, str(mx).zfill(4))
            case_name = 'case_order%s_mx%s' % (order, str(mx).zfill(4))

            setrun_params = {}
            setrun_params['clawdata.order'] = order
            setrun_params['clawdata.num_cells'] = [mx]

            case['outdir'] = outdir
            case['case_name'] = case_name
            case['setrun_params'] = setrun_params

            caselist.append(case)

    return caselist



if __name__ == '__main__':

    # number of GeoClaw jobs to run simultaneously:
    nprocs = 4

    caselist = make_cases()

    multiprocessing.log_to_stderr(logging.INFO)

    # run all cases using nprocs processors:
    multip_tools.run_many_cases_pool(caselist, nprocs, run_one_case)
