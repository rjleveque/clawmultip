"""
Code to run several similar cases over mulitple processors using the
Python multiprocess module.

The main function provided is
    run_many_cases(caselist, nprocs, run_one_case)
which takes a list of cases to run, the number of processors to use, and
a function that runs a single case as input.

*caselist* is a list of dictionaries.  
Each dictionary should define whatever parameters are needed for one case.

This module contains templates run_one_case_sample and make_all_cases_sample.
If you execute:
    python multip_tools.py 3
at the command line, for example, these will be used to do a quick example
with nprocs=3, where run_one_case_sample is used to simply print out a case
number and make_all_cases_sample makes 7 such cases.

The example code run_one_case_dtopo and make_all_cases_dtopos
can be used to do a set of GeoClaw runs with a different dtopo file for
each run, and otherwise identical parameters contained in a setrun.py
that is assumed to exist.
"""

from numpy import *
import os, time, shutil, sys
from multiprocessing import Process, current_process


setplot_file = os.path.abspath('setplot.py')

def run_many_cases(caselist, nprocs, run_one_case):
    """
    Split up cases in *caselist* between the *nprocs* processors.
    Each case is a dictionary of parameters for that case.

    *run_one_case* should be a function with a single input *case*
    that runs a single case. 
    """

    # Split up cases between nprocs processors:
    # caseproc[i] will be a list of all cases to be handled by processor i
    caseproc = [[] for p in range(nprocs)]
    for i in range(len(caselist)):
        caseproc[i%nprocs].append(caselist[i])

    # for debugging:
    #print("+++ caseproc: ", caseproc)

    abort_time = 5
    print("\n%s cases will be run on %s processors" % (len(caselist),nprocs))
    print("You have %s seconds to abort..." % abort_time)

    time.sleep(abort_time) # give time to abort

    if 0:
        ans = raw_input("OK to run? ")
        if ans.lower() not in ['y','yes']:
            raise Exception("*** Aborting")
    

    def run_cases(procnum):
        # loop over all cases assigned to one processor:
        p = current_process()
        message =  "\nProcess %s will run %s cases\n" \
                    % (p.pid, len(caseproc[procnum]))
        if 0:
            # print dictionary for each case, useful for debugging:
            for case in caseproc[procnum]:
                message = message + "  %s \n" % case
        print(message) # constructed first to avoid interleaving prints
        time.sleep(1)

        for case in caseproc[procnum]:
            run_one_case(case)

    plist = [Process(target=run_cases, args=(p,)) for p in range(nprocs)]

    # Handle termination of subprocesses in case user terminates the main process
    def terminate_procs():
        for P in plist:
            if P.is_alive():
                P.terminate()
    # If this is registered, all processes will die if any are killed, e.g.
    # if ctrl-C received, but also if python exception encountered in
    # postprocessing of any run...
    #atexit.register(terminate_procs)

    print("\n=========================================\n")
    for P in plist:
        P.start()
        print("Starting process: ",P.pid)
    for P in plist:
        P.join()

def run_many_cases_pool(caselist, nprocs, run_one_case):
    """
    Use multiprocessing.Pool in this version, rather than pre-assigning
    cases to processes.  Should work better if some take longer to run
    than others.
    
    Split up cases in *caselist* between the *nprocs* processors.
    Each case is a dictionary of parameters for that case.

    *run_one_case* should be a function with a single input *case*
    that runs a single case. 
    """
    
    from multiprocessing import Pool, TimeoutError

    abort_time = 5
    print("\n%s cases will be run on %s processors" % (len(caselist),nprocs))
    print("You have %s seconds to abort..." % abort_time)

    time.sleep(abort_time) # give time to abort
        
    with Pool(processes=nprocs) as pool:
        pool.map(run_one_case, caselist)
        
        

def make_all_cases_sample():
    """
    Output: *caselist*, a list of cases to be run.
    Each case should be dictionary of any parameters needed to set up an
    individual case.  These will be used by run_one_case.

    This is a sample where each case has a single parameter 'num'.
    Specialize this code to the problem at hand.
    """

    # Create a list of the cases to be run:
    caselist = []
    num_cases = 7

    for num in range(num_cases):
        case = {'num': num}
        caselist.append(case)

    return caselist


def run_one_case_sample(case):
    """
    Generic code, must be specialized to the problem at hand.
    Input *case* should be a dictionary with any parameters needed to set up
    and run a specific case.
    """

    # For this sample, case['num'] is just an identifying number.
    print('Sample job... now running case ',case['num'])
    
    # This part shows how to redirect stdout so output from any
    # print statements go to a unique file...
    import sys
    import datetime
    
    message = ""
    stdout_fname = 'case%s_out.txt' % case['num']
    try:
        stdout_file = open(stdout_fname, 'w')
        message = message +  "Python output from this case will go to %s\n" \
                            % stdout_fname
    except:
        raise Exception("Cannot open file %s" % stdout_fname)
        
    sys_stdout = sys.stdout
    sys.stdout = stdout_file
    # send any errors to the same file:
    sys_stderr = sys.stderr
    sys.stderr = stdout_file
    
    
    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    print('Working on case %s, started at %s' % (case['num'],timenow))

    p = current_process()
    print('Process running this case: ', p)
    
    # replace this with something useful:
    sleep_time = 2
    print("Will sleep for %s seconds..." % sleep_time)
    time.sleep(sleep_time)
    
    if 0:
        # throw an error to check that output:
        time.no_such_function()
    
    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    print('Done with case %s at %s' % (case['num'],timenow))
    
    # Reset stdout and stdout:
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr


def make_all_cases_dtopos(dtopo_dir, dtopo_names, xgeoclaw_path, runs_dir='.'):
    """
    Output: *caselist*, a list of cases to be run.
    Each case should be dictionary of any parameters needed to set up an
    individual case.  These will be used by run_one_case_dtopo.
             
    For this example, each dtopo_name in dtopo_names corresponds to a dtopo
    file.  GeoClaw will be run for each of these earthquake sources.
    A unique directory will be created for each run, with names
    based on dtopo_name, and residing within runs_dir.
    The _output and _plots directories will be within the run directory.

    """

    # Create a list of the cases to be run:
    caselist = []

    for dtopo_name in dtopo_names:
        dtopofile = os.path.join(dtopo_dir, '%s.dtt3' % dtopo_name)

        # Create all directories needed first, in case there's a problem:

        runs_dir = os.path.abspath(runs_dir)
        outdir = os.path.join(runs_dir, 'geoclaw_outputs/_output_%s' \
                    % dtopo_name)
        plotdir = os.path.join(runs_dir, 'geoclaw_plots/_plots_%s' \
                    % dtopo_name)
        os.system('mkdir -p %s' % outdir)
        print('Created %s' % outdir)
        os.system('mkdir -p %s' % plotdir)
        print('Created %s' % plotdir)
        
        # Define a dictionary of the parameters needed for this case:
        case = {'dtopo_name':dtopo_name, 'dtopofile':dtopofile,
                'outdir':outdir, 'plotdir':plotdir, 
                'xgeoclaw_path':xgeoclaw_path}
        caselist.append(case)

    return caselist



def run_one_case_dtopo(case):
    """
    Input *case* should be a dictionary with any parameters needed to set up
    and run a specific case.
    
    In this example, it is assumed that all values in setrun.py will be
    used for every run with the exception of the dtopo file.
    """

    import datetime
    from clawpack.clawutil.runclaw import runclaw
    from clawpack.visclaw.plotclaw import plotclaw
    from setrun import setrun  # setrun.py should exist in run directory

    p = current_process()
    
    # unpack the dictionary:
    dtopo_name = case['dtopo_name']
    dtopofile = case['dtopofile']
    outdir = case['outdir']
    xgeoclaw_path = case['xgeoclaw_path']
    plotdir = case['plotdir']

    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    message = "Process %i started   case %s at %s\n" \
                % (p.pid, dtopo_name, timenow)
    
    if not os.path.isdir(outdir):
        print(message)
        raise Exception("Missing directory: %s" % outdir)
    
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

    
    # initialize rundata using setrun but then change some things for each run:
    rundata = setrun()

    rundata.dtopo_data.dtopofiles = [[3, dtopofile]]

    topdir = os.getcwd()

    try:
        os.chdir(outdir)
    except:
        raise Exception("*** Cannot chdir into %s" % outdir)

    rundata.write()
    os.chdir(topdir)

    # Run the xgeoclaw code
    # Use data from rundir=outdir, which was just written above...
    runclaw(xclawcmd = xgeoclaw_path, outdir=outdir, 
            rundir=outdir, nohup=False)

    if 0:
        # also make plots for each:
        print("Plotting results in %s" % outdir)
        print("Plotting using ",setplot_file)
        plotclaw(outdir, plotdir, setplot_file)

    stdout_file.close()
    # Fix stdout again
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr

    timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    message = "Process %i completed case %s at %s\n" \
                % (p.pid, dtopo_name, timenow)
    print(message)

if __name__ == "__main__":
    
    # Sample code...

    if len(sys.argv) > 1:
        nprocs = int(sys.argv[1])
    else:
        nprocs = 1

    caselist = make_all_cases_sample()
    run_many_cases_pool(caselist, nprocs, run_one_case=run_one_case_sample)
    print("Done... See files caseN_out.txt for python output from each case")
