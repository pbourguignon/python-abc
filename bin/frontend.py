#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A frontend to the python-abc library.

Assumes that the user provides a module exposing the following methods:
- prior_r() 
    When called they should return a sample parameter drawn from the prior
- statistics_r(params)
    When called with a parameter, returns a sample of the summarizing 
    statistics
- load_params(filename)
    Loads the hyperparameters and returns them for use as an argument of
    prior_r
- load_data(filename)
    Loads the data and returns their summary statistics
- format(params)
    Will be used to print the results

python-abc is free software, distributed under the GPL license.

This file was created on Fri Feb 28 20:10:13 2014

@author: P.-Y. Bourguignon <pbourguignon@isthmus.fr>
"""

import sys
import os
import datetime
import argparse
import ConfigParser
import ABCmp

F_NAMES=["prior", "stat", "load-params", "load-data", "format"]

def debug(msg):
    pass

def init():
    
    options = [(["-m", "--module"],
                {"help": "Path to the user module",
                 "required": False}),
               (["--prior"],
                {"help": "Prior sampling function (default; prior_r)"}),
               (["--stat"],
                {"help": "Statistics sampling function (default: stat_r)"}),
               (["--load-params"],
                {"help": "Hyperparameters loading functions (default: load_params)",
                 "dest": "load-params"}),
               (["--load-data"],
                {"help": "Data loading function (default: load_data)",
                 "dest": "load-data"}),
               (["--format"],
                {"help": "Parameters printing function (default: format)"}),
               (["-p","--params"],
                {"help": "Hyperparameters file",
                 "required": True}),
               (["-d", "--data"],
                {"help": "Data file",
                 "required": True}),
               (["-n", "--nsamples"],
                {"help": "sample size",
                 "required": True, "type": int}),
               (["-r", "--ratio"],
                {"help": "Proportion of closest samples to keep",
                 "required": True, "type": float}),
               (["-c", "--ncpus"],
                {"help": "Number of processes (default: autodetect)",
                 "type": int}),
               (["-v", "--verbose"],
                {"help": "Turn on log output",
                 "action": "store_true"})]
    parser = argparse.ArgumentParser(description="""
        This program runs Approximate Bayesian Computation (ABC) simulations, 
        calling user-provided functions for model-dependent operations (like
        sampling parameters from the prior, or statistics given parameters).
        
        A configuration file named .abcrc will be searched in the working
        directory, and the corresponding options loaded with lower priority
        than the command-line options.
        """)
    for opt in options:
        parser.add_argument(*opt[0],**opt[1])

    settings = {}

    try:
        cfg = ConfigParser.ConfigParser()
        cfg.read(".abcrc")
        for k in cfg.options("core"):
            settings[k] = cfg.get("core", k)
    except:
        sys.stderr.write("No config file found\n")
        sys.stderr.flush()

    options = vars(parser.parse_args())
    
    for opt in options.keys():
        if options[opt] is not None:
            settings[opt] = options[opt]
    
    summary  = "\nABCmp running on %s at %s\n\n" % (os.uname()[1], 
                                             str(datetime.datetime.now()))
    summary += "  Data file:\t\t%s\n" % settings['data']
    summary += "  Hyperparameters file:\t%s\n" % settings['params']
    summary += "  Module file:\t\t%s\n" % settings['module']
    summary += "  Sample size:\t\t%i\n" % settings['nsamples']
    summary += "  Acc. ratio:\t\t%f\n" % settings['ratio']
    summary += "\n"
    sys.stderr.write(summary) 

    if settings['verbose']:
        def verbose_debug(msg):
            sys.stderr.write("[" + str(datetime.datetime.now())+"] " + msg)
            sys.stderr.flush()
        globals()['debug'] = verbose_debug
        ABCmp.debug = verbose_debug
    
    f_user_names = {k: settings[k] for k in F_NAMES}
    functions = load_user_module(settings['module'], f_user_names)
    
    if not settings.has_key("ncpus"):
        debug("Detecting number of CPUs...\r")    
        settings["ncpus"] = ABCmp.multiprocessing.cpu_count()
        debug("Detected %i CPUs            \n" % settings["ncpus"] )
    
    return settings, functions

def load_user_module(filename, f_user_names):
    path = os.path.dirname(os.path.abspath(filename))
    module_basename = os.path.basename(filename)
    module_name, ext = os.path.splitext(module_basename)
        
    try:
        sys.path.insert(0, path)
        umodule = __import__(module_name, 
                             globals(), locals(),
                             [])
    except:
        print "Could not import module %s" % module_name
        exit(0)

    functions = {k: umodule.__getattribute__(f_user_names[k])\
                        for k in F_NAMES}
    
    return functions

if __name__ == '__main__':
    options, functions = init()
    
    debug("Loading data...\r")    
    data_summary = functions['load-data'](options['data'])
    debug("Data loaded      \n")
    debug("Loading hyperparameters...\r")
    hparams = functions['load-params'](options['params'])
    debug("Hyperparameters loaded     \n")

    debug("Instantiating sampler...\r")    
    sampler = ABCmp.ABCmp(data_summary, lambda: functions["prior"](hparams),
                          functions["stat"], nworkers=options['ncpus'])
    debug("Sampler instantiated     \n")
    debug("Running sampler...\n")
    for res in sampler.sample(options['nsamples'], options['ratio']):
        print functions["format"](res)
    debug("Sampling finished, bye!\n")