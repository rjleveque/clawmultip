from clawpack.clawutil import runclaw

import multip_tools
import os,sys,shutil,pickle
#import contextlib



def run_one_case_clawpack(case):
    """
    Input *case* should be a dictionary with any parameters needed to set up
    and run a specific case.

    It is assumed that all values in setrun.py will be
    used for every run with the exception of the parameters set for each case.
    """

    import datetime
    from clawpack.clawutil.runclaw import runclaw

    #from clawpack.visclaw.plotclaw import plotclaw
    # for now use local version:
    import os,sys
    CLAW = os.environ['CLAW']
    sys.path.insert(0, CLAW + '/clawmultip/src/python/clawmultip')
    from plotclaw import plotclaw
    sys.path.pop(0)

    from plotclaw import plotclaw

    from clawpack.visclaw.plotpages import plotclaw2html
    import importlib
    import os,sys,shutil,pickle
    from multiprocessing import current_process


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
        #rundata = setrun.setrun()

        # setrun function to be called from must be modified to accept
        # a parameter `case` so that the dictionary of parameters can be
        # passed in.

        # setrun must be modified to accept case as a kwarg in order to
        # customize for each case:
        rundata = setrun.setrun(case=case)

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

        # setplot must be modified to accept case as a kwarg in order to
        # customize for each case:
        plotdata = setplot.setplot(plotdata=None,case=case)

        if plotdata is not None:
            # user wants to make time frame plots using plotclaw:
            plotdata.outdir = outdir
            plotdata.plotdir = plotdir

            # modified plotclaw is needed in order to pass plotdata here:
            plotclaw(outdir, plotdir, plotdata=plotdata)
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
