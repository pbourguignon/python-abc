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
import argparse
import ABCmp

F_NAMES=["prior", "stat", "load_params", "load_data", "format"]

def init():
    
    options = [(["-m", "--module"],
                {"help": "Path to the user module",
                 "required": True}),
               (["--prior"],
                {"help": "Prior sampling function",
                 "default": "prior_r"}),
               (["--stat"],
                {"help": "Statistics sampling function",
                 "default": "statistics_r"}),
               (["--load-params"],
                {"help": "Hyperparameters loading functions",
                 "default": "load_params"}),
               (["--load-data"],
                {"help": "Data loading function",
                 "default": "load_data"}),
               (["--format"],
                {"help": "Parameters printing function",
                 "default": "format_param"}),
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
                {"help": "Number of processes (defaults to 1)",
                 "type": int, "default": 1})]
    parser = argparse.ArgumentParser(description="""
        This program runs Approximate Bayesian Computation (ABC) simulations, 
        calling user-provided functions for model-dependent operations (like
        sampling parameters from the prior, or statistics given parameters).
        """)
    for opt in options:
        parser.add_argument(*opt[0],**opt[1])

    settings = parser.parse_args()
    
    f_user_names = {k: settings.__getattribute__(k) for k in F_NAMES}
    functions = load_user_module(settings.module, f_user_names)
    
    return settings, functions

def load_user_module(filename, f_user_names):
    path = os.path.dirname(os.path.abspath(filename))
    module_basename = os.path.basename(filename)
    module_name, ext = os.path.splitext(module_basename)
        
    try:
        sys.path.insert(0, path)
        umodule = __import__(module_name, 
                             globals(), locals(),
                             f_user_names)
    except:
        print "Could not import module %s" % module_name
        exit(0)
    
    functions = {k: umodule.__getattribute__(f_user_names[k])\
                        for k in F_NAMES}
    
    return functions

if __name__ == '__main__':
    options, functions = init()
        
    data_summary = functions['load_data'](options.data)
    hparams = functions['load_params'](options.params)    
    
    sampler = ABCmp.ABCmp(data_summary, lambda: functions["prior"](hparams),
                          functions["stat"], nworkers=options.ncpus)
    for res in sampler.sample(options.nsamples, options.ratio):
        print functions["format"](res)
