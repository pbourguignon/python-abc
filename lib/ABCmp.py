# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 15:43:00 2014

@author: P.-Y. Bourguignon - pbourguignon@isthmus.fr
"""

import multiprocessing
from ctypes import c_int, c_double
from timeit import Timer
import sys
import os
import importlib

def debug(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()

class ABCmp(object):
    def __init__(self, data_summary, f_prior, f_statistics, nworkers=2):
        self.nworkers = nworkers
        self.f_prior, self.f_statistics = f_prior, f_statistics
        self.data_summary = data_summary
        self.f_distance = self.learn_distance()

    def learn_distance(self, size=100):
        samples = [self.f_statistics(self.f_prior()) \
                    for ii in range(size)]
        w = {}
        for k in self.data_summary.keys():
            component = [s[k] for s in samples]
            ssq = sum([(c-self.data_summary[k])**2 for c in component])
            w[k]=ssq/len(component)
            #sys.stdout.write("Weight "+ str(k)+ ": "+ str(w[k])+"\n")
        return (lambda s: sum([(s[k]-v)**2/w[k] \
                            for k,v in self.data_summary.iteritems()]))
        
    def sample(self, nsamples, acc_ratio, queue_size=1000):
        ntest = max(1000, int(2.0/acc_ratio))
        samples = [self.f_distance(self.f_statistics(self.f_prior()))\
                    for ii in range(ntest)]
        
        s_samples = sorted(samples)

        queue = multiprocessing.Queue(queue_size)
        t_high = multiprocessing.RawValue(c_double, 
                                          s_samples[int(2*ntest*acc_ratio)])
        ndiscards = [multiprocessing.Value(c_int, 0)\
                        for ii in range(self.nworkers)]
        workers = [Sampler(queue, ndiscards[ii], t_high,
                           self.f_prior, 
                           self.f_statistics, 
                           self.f_distance)
                                for ii in range(self.nworkers)]
        
        for w in workers:
            w.start()

        samples = []
        
        debug("Starting sampling...\n")
        nvalids = 0
        clock = Timer()
        log_time = clock.timer()
        while True:
            now = clock.timer()
            if now - log_time > .1:
                log_time = now
                nd = sum([ndiscards[ii].value for ii in range(self.nworkers)])
                ndraws = nd + nvalids
                debug("\rSampling " + 
                     str(int(ndraws / (nsamples/100))) + 
                     "% complete")
                if ndraws > nsamples:
                    break
            
            params, dist = queue.get()
            nvalids += 1
            samples.append((params, dist))
            
        for w in workers:
            w.terminate()
        debug("\rSampling completed      \n")
        debug("Queue size: " + str(nvalids) + '\n')
        #TODO
        # Make sure the queue is fully consumed, otherwise
        # sample statistics are invalid
        results = [x[0] for x in sorted(samples,\
                                       key=lambda x: x[1])[0:int(nsamples*acc_ratio)]]
        return results

    

class Sampler(multiprocessing.Process):
    def __init__(self, queue, ndiscards, t_high,
                 f_prior, f_statistics, f_distance):
        multiprocessing.Process.__init__(self)
        self.queue, self.ndiscards, self.t_high = \
                            queue, ndiscards, t_high
        self.f_prior, self.f_statistics, self.f_distance = \
                            f_prior, f_statistics, f_distance
        
        
    def run(self):
        while True:
            params = self.f_prior()
            dist = self.f_distance(self.f_statistics(params))
            if dist < self.t_high.value:
                self.queue.put((params, dist))
            else:
                self.ndiscards.value += 1
            
if __name__ == '__main__':
    nsamples = int(sys.argv[1])
    acc_ratio = float(sys.argv[2])
    ncpus = int(sys.argv[3])
    mod_path = os.path.dirname(sys.argv[4])
    sys.path.append(mod_path)    
    mod = importlib.import_module(os.path.basename(sys.argv[4].replace(".py","")))
    
    # Data in the form of x_hat
    data = {'x_hat': [1.05,
                      0.95,1.03,
                      .92,.99,.98,1.03,
                      .98,.91,.95,1.04,1.1,0.99,1.06,.99]}
                      
    h_params = {'mu_x':    (1.25,1.1),
                'sigma_x2':(5, .02),
                'beta_y':  (2.0,10),
                'beta_o':  (2.0,10),}

    sampler = ABCmp(mod.lt_summarize(data), lambda: mod.lt_prior(h_params), lambda x: mod.lt_summarize(mod.lt_noisy_obs(mod.lt_model(x,4))), nworkers=ncpus)
    res = sampler.sample(nsamples,acc_ratio)
    for val in res:
        print mod.lt_format(val)
