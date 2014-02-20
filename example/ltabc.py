# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 14:38:08 2014

@author: P.-Y. Bourguignon - pbourguignon@isthmus.fr
"""

import ABC
import lineageTree as lt
import math
import sys

if __name__ == '__main__':
    
    n_samples = int(sys.argv[1])
    ratio = float(sys.argv[2])

    data = {}
    data['x_hat'] = lt.lt_load_data('data/test.dat')
    h_params = lt.lt_load_h_params('data/h_params.dat')
    nb_generations = int(math.log(len(data['x_hat'])+1, 2))
    #print "Nb generations: ", nb_generations
    
    abc = ABC.ABCSampler(data, 
                     lambda: lt.lt_prior(h_params),
                     lambda param: lt.lt_noisy_obs(lt.lt_model(param, nb_generations)),
                     lt.lt_summarize)

    samples = abc.sample(n_samples, ratio)
    
    for sample in samples:
        print lt.lt_format(sample)