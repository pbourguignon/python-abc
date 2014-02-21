# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 13:24:49 2014

@author: P.-Y. Bourguignon - pbourguignon@isthmus.fr
"""
from random import randint, gammavariate, betavariate, normalvariate
import json
import sys

def _gauss_pos(mean, std):
    while True:
        x = normalvariate(mean, std)
        if x > 0:
            return x

def lt_prior(h_params2):
    """
    Parameters
    ----------
    h_params    a hashmap with the hyperparameters
    
    Returns
    -------
    A realization of the parameter 
    """
    
    while True:
        param = {'mu_x':       _gauss_pos(*h_params2['mu_x']),
            'sigma_x2':   gammavariate(*h_params2['sigma_x2']),
            'beta_y':     gammavariate(*h_params2['beta_y']),
            'beta_o':     gammavariate(*h_params2['beta_o']),}
        if param['beta_y'] < param['beta_o']:
            return param

def lt_model(params, nb_generations):
    """
    Sample from the lineage tree model
    
    Parameter
    ---------

    params          A parameter hashmap generated from the prior
    nb_generations  The number of generations in the lineage
    
    Returns
    -------

    A dict holding a realization of the increments, splits, and deltas
    """
    nb_splits =     2**(nb_generations - 1) - 1
    nb_increments = 2**nb_generations - 1
    increments =    [_gauss_pos(params['mu_x'], params['sigma_x2']) \
                        for ii in range(nb_increments)]
    splits =        [betavariate(params['beta_y'], params['beta_o']) \
                        for ii in range(nb_splits)]
    delta =         [randint(0,1) for ii in range(nb_splits)]
                                                                                    
    return { 'incr': increments, 'splits': splits, 'delta': delta }





def lt_noisy_obs(obs, shape = 10):
    """
    Parameters
    ----------
    obs            A realization of the hidden variable
    shape		  The shape parameter of the added noise
	
    Returns
    -------
    xb, xd         The path of the hidden variables
    inc, splits    Noisy observations
    """
    
    nb_cells = len(obs['incr'])
    nb_splits = len(obs['splits'])
    
    xb = [None]*nb_cells
    xd = [None]*nb_splits
    g = [None]*nb_cells ### the growth /gamma 
    
    xb[0] = 1.0
    
    for ii in range(nb_splits):
        xd[ii] = xb[ii] + obs['incr'][ii]                
        xb[2*ii+1+obs['delta'][ii]] = xd[ii]*obs['splits'][ii]
        xb[2*ii+2-obs['delta'][ii]] = xd[ii]-xb[2*ii+1+obs['delta'][ii]]

    growth_rate = [gammavariate(shape, 1.0/(x+sys.float_info.epsilon)) for x in xb]
    
    x_hat = [shape/g for g in growth_rate]
    
           	
    return {'xb': xb, 'xd': xd, 'x_hat': x_hat }
   
   
   
def lt_summarize(obs): 
    """
    Parameter
    ---------
    
    obs         A dict holding 
        - x_hat     An array of reconstrubted x_hat from observations
                       
    Returns
    -------
    
    A dict of average and variance of increments and splits
   
    """
    x_hat = obs['x_hat']
    nb_splits = (len(x_hat)+1)/2-1
    
    incr = [x_hat[2*ii+1]+x_hat[2*ii+2]-x_hat[ii] for ii in range(nb_splits)]
    splits = [min(x_hat[2*ii+1], x_hat[2*ii+2])/(x_hat[2*ii+1]+x_hat[2*ii+2]) \
                    for ii in range(nb_splits)]

    incr_avg = sum(incr)/len(incr)
    incr_var = sum([(v - incr_avg)**2 for v in incr])/ \
                    (len(incr)-1)

    split_avg = sum(splits)/len(splits)
    split_var = sum([(v-split_avg)**2 for v in splits])/\
                    (len(splits)-1)
    
    return { 'incr_avg': incr_avg, 'incr_var': incr_var,
             'split_avg': split_avg, 'split_var': split_var }
   
def lt_load_data(filename):
    """
    Reads the x_hat from a file, as indexed in the observation table
    Recommended layout:
        x_1
        x_2 x_3
        x_4 x_5 x_6 x_7
        ...
    """
    data = []
    with open(filename) as f:
        for l in f.readlines():
            data += [float(x) for x in l.split()]
    return data

def lt_load_h_params(filename):
    """
    Reads the hyperparameters from a JSON file
    """
    with open(filename) as f:
        content = ''.join(f.readlines())
        #print content
    return json.loads(content)

def lt_format(params):
    return "%(mu_x)s\t%(sigma_x2)s\t%(beta_y)s\t%(beta_o)s" % params
    

        