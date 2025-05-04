"""
The function run_one_case_clawpack defined in this module can be used when
calling mulitp_tools.run_many_cases_pool, along with a list of cases,
in order to perform a parameter sweep using Clawpack.
"""


def run_one_case_clawpack(case):
    """
    Code to run a specific case and/or plot the results using Clawpack.
    This function can be pased in to multip_tools.run_many_cases_pool
    along with a list of cases to perform a parameter sweep based on the cases.

    Input *case* should be a dictionary with any parameters needed to set up
    and run a specific case and/or plot the results.

    It is assumed that values specified by the setrun function provided
    will be used for every run, with the exception of the parameters
    set for each case, and similarly for setplot.

    In order to pass the case into setrun and/or setplot to modify the desired
    parameters, you can provide functions that include an additional
    parameter case.

    For sample code that sets up a list of cases with modified setrun and
    setplot functions, see
        $CLAW/clawutil/examples/clawmultip_advection_1d_example
    and the README.txt file in that directory.

    This function assumes that, in addition to any parameters you want to
    modify for your parameter sweep, the case dictionary includes the following:

        case['xclawcmd'] = path to the Clawpack executable to perform each run
                           or None if you do not want to run Clawpack
                              (in order to only make a new set of plots based
                              on existing output).

        case['outdir'] = path to _output directory for this run
        case['plotdir'] = path to _plots directory for this run,
                          or None if you do not want to make plots.
        case['setrun_file'] = path to setrun_cases.py, which contains a
                              function setrun(claw_pkg, case)
                              so that case can be passed in.
                              (Only needed if case['xclawcmd'] is not None)
        case['setplot_file'] = path to setplot_cases.py, which contains a
                              function setplot(plotdata, case)
                              so that case can be passed in (if desired, or
                              a standard setplot(plotdata) can be used if it
                              is independent of the case).
                              (Only needed if case['plotdir'] is not None)

        The following are optional:

        case['overwrite'] = True/False.  Aborts if this is False
                            and case['outdir']  exists.  (Default is True)
        case['runexe'] = Any string that must preceed xclawcmd to run the code
        case['nohup'] = True to run with nohup. (Default is False)
        case['redirect_python'] = True/False. Redirect stdout to a file
                                  case['outdir'] + '/python_output.txt'
                                  (Default is True)

        In addition, add any other parameters to the case dictionary that
        you want to have available in setrun and/or setplot.

    """

    import multip_tools
    import os,sys,shutil,pickle
    import inspect
    import datetime
    import importlib
    from multiprocessing import current_process
    from clawpack.clawutil.runclaw import runclaw

    #from clawpack.visclaw.plotclaw import plotclaw
    # for now use local version:
    import os,sys
    CLAW = os.environ['CLAW']
    sys.path.insert(0, CLAW + '/clawmultip/src/python/clawmultip')
    from plotclaw import plotclaw
    sys.path.pop(0)

    p = current_process()

    # unpack the dictionary case to get parameters for this case:

    xclawcmd = case.get('xclawcmd', None)
    run_clawpack = xclawcmd is not None

    plotdir = case.get('plotdir', None)
    make_plots = plotdir is not None

    case_name = case['case_name']
    outdir = case['outdir']
    setrun_file = case.get('setrun_file', 'setrun.py')
    setplot_file = case.get('setplot_file', 'setplot.py')

    # clawpack.clawutil.runclaw parameters that might be specified:
    overwrite = case.get('overwrite', True) # if False, abort if outdir exists
    runexe = case.get('runexe', None)  # string that must preceed xclawcmd
    nohup = case.get('nohup', False)  # run with nohup

    redirect_python = case.get('redirect_python', True) # sent stdout to file


    if os.path.isdir(outdir):
        print('overwrite = %s and outdir already exists: %s' \
                % (overwrite,outdir))
        # note that runclaw will use overwrite parameter to see if allowed
    else:
        try:
            os.mkdir(outdir)
            print('Created %s' % outdir)
        except:
            raise Exception("Could not create directory: %s" % outdir)


    #timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    timenow = datetime.datetime.utcnow().strftime('%Y-%m-%d at %H:%M:%S') \
                + ' UTC'
    message = "Process %i started   case %s at %s\n" \
                % (p.pid, case_name, timenow)
    print(message)


    if redirect_python:
        stdout_fname = outdir + '/python_output.txt'
        try:
            stdout_file = open(stdout_fname, 'w')
            message = "Python output from this run will go to\n   %s\n" \
                                % stdout_fname
        except:
            print(message)
            raise Exception("Cannot open file %s" % stdout_fname)


        # Redirect stdout,stderr so any print statements go to a unique file...
        import sys
        sys_stdout = sys.stdout
        sys.stdout = stdout_file
        sys_stderr = sys.stderr
        sys.stderr = stdout_file
        print(message)

    # write out all case parameters:
    fname = os.path.join(outdir, 'case_info.txt')
    with open(fname,'w') as f:
        f.write('----------------\n%s\n' % timenow)
        f.write('case %s\n' % case['case_name'])
        for k in case.keys():
            f.write('%s:  %s\n' % (k.ljust(20), case[k]))
    print('Created %s' % fname)

    # pickle case dictionary for reloading later:
    fname = os.path.join(outdir, 'case_info.pkl')
    with open(fname, 'wb') as f:
        pickle.dump(case, f)
    print('Created %s' % fname)

    # global summary file:
    fname = 'case_summary.txt'
    with open(fname,'a') as f:
        f.write('=========\n%s\n\ncase_name: %s\n' % (timenow,case['case_name']))
        for k in case.keys():
            if k != 'case_name':
                f.write('%s:  %s\n' % (k.ljust(20), case[k]))


    if run_clawpack:

        # initialize rundata using specified setrun file:
        spec = importlib.util.spec_from_file_location('setrun',setrun_file)
        setrun = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setrun)

        # The setrun function may have been modified to accept an argument
        # `case` so that the dictionary of parameters can be passed in:

        if 'case' in inspect.signature(setrun.setrun).parameters.keys():
            rundata = setrun.setrun(case=case)
        else:
            print('*** Warning: setrun does not support case parameter: ', \
                    '    setrun_file = %s' % setrun_file)
            rundata = setrun.setrun()

        # write .data files in outdir:
        rundata.write(outdir)

        # Run the clawpack executable
        if not os.path.isfile(xclawcmd):
            raise Exception('Executable %s not found' % xclawcmd)

        # redirect output and error messages:
        outfile = os.path.join(outdir, 'fortran_output.txt')
        print('Fortran output will be redirected to\n    ', outfile)

        # Use data from rundir=outdir, which was just written above...
        runclaw(xclawcmd=xclawcmd, outdir=outdir, overwrite=overwrite,
                rundir=outdir, nohup=nohup, runexe=runexe,
                xclawout=outfile, xclawerr=outfile)

    if make_plots:

        # initialize plotdata using specified setplot file:
        spec = importlib.util.spec_from_file_location('setplot',setplot_file)
        setplot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setplot)

        # The setplot function may have been modified to accept an argument
        # `case` so that the dictionary of parameters can be passed in:

        if 'case' in inspect.signature(setplot.setplot).parameters.keys():
            plotdata = setplot.setplot(plotdata=None,case=case)
        else:
            print('*** Warning: setplot does not support case parameter: ', \
                    '    setplot_file = %s' % setplot_file)
            plotdata = setplot.setplot(plotdata=None)


        # note that setplot can also be modified to return None if the
        # user does not want to make frame plots (setplot can explicitly
        # make other plots or do other post-processing)

        if plotdata is not None:
            # user wants to make time frame plots using plotclaw:
            plotdata.outdir = outdir
            plotdata.plotdir = plotdir

            # modified plotclaw is needed in order to pass plotdata here:
            plotclaw(outdir, plotdir, setplot, plotdata=plotdata)
        else:
            # assume setplot already made any plots desired by user,
            # e.g. fgmax, fgout, or specialized gauge plots.
            print('plotdata is None, so not making frame plots')

    #timenow = datetime.datetime.today().strftime('%Y-%m-%d at %H:%M:%S')
    timenow = datetime.datetime.utcnow().strftime('%Y-%m-%d at %H:%M:%S') \
                + ' UTC'
    message = "Process %i completed case %s at %s\n" \
                % (p.pid, case_name, timenow)
    print(message)

    if redirect_python:
        stdout_file.close()
        # Fix stdout again
        sys.stdout = sys_stdout
        sys.stderr = sys_stderr
        print(message) # to screen


def make_cases_template():

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

            #case['xclawcmd'] = None  # if None, will not run code
            case['xclawcmd'] = 'xclaw'  # executable created by 'make .exe'

            # setrun parameters:
            case['setrun_file'] = 'setrun_cases.py'
            # setrun_case.py should contain a setrun function with case
            # as a keyword argument so we can pass in the following values:

            case['order'] = order
            case['mx'] = mx

            #case['plotdir'] = None  # if None, will not make plots
            case['plotdir'] = outdir.replace('_output', '_plots')
            case['setplot_file'] = 'setplot_cases.py'

            # no setplot parameters are set here for this example,
            # instead setplot_cases.setplot has a case argument and uses it
            # to get outdir and case_name used in the title of figures

            caselist.append(case)

    return caselist
