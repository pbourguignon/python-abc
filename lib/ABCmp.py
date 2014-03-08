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
    pass

class ABCmp(object):
    def __init__(self, data_summary, f_prior, f_statistics, f_distance=None, nworkers=2):
        self.nworkers = nworkers
        self.f_prior, self.f_statistics = f_prior, f_statistics
        self.data_summary = data_summary
        if f_distance is None:
            self.f_distance = self.learn_distance()
        else:
            self.f_distance = lambda x: f_distance(data_summary, x)

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
        
        queue = multiprocessing.Queue(queue_size)
        t_high = multiprocessing.Value(c_double, sys.float_info.max)
        ndiscards = [multiprocessing.Value(c_int, 0)\
                        for ii in range(self.nworkers)]
        workers = [Sampler(queue, ndiscards[ii], t_high,
                           self.f_prior, 
                           self.f_statistics, 
                           self.f_distance)
                                for ii in range(self.nworkers)]
        for w in workers:
            w.start()
        
        debug("Starting calibration of the queue...\n")
                            
        ntest = max(1000, int(2.0/acc_ratio))
        samples = [queue.get()[1] for ii in range(ntest)]

        debug("Calibration done\n")        
        
        t_high.value = sorted(samples)[int(2*ntest*acc_ratio)]
        samples = []
        
        debug("Starting sampling\n")        
        
        nvalids = 0
        clock = Timer()
        log_time = clock.timer()
        while True:
            now = clock.timer()
            if now - log_time > .1 :
                log_time = now
                nd = sum([ndiscards[ii].value for ii in range(self.nworkers)])
                ndraws = nd + nvalids
                debug("Sampling " + 
                     str(int(ndraws / (nsamples/100))) + 
                     "% complete\r")
                if ndraws > nsamples:
                    break
            
            params, dist = queue.get()
            nvalids += 1
            samples.append((params, dist))
            
        for w in workers:
            w.terminate()

        debug("Sampling completed              \n")
        debug("Queue size: " + str(nvalids) + '\n')
        #TODO
        # Make sure the queue is fully consumed, otherwise
        # sample statistics are invalid
        if len(samples) < nsamples*acc_ratio:
            raise BufferError("Incomplete sample, only %i available" % len(samples))

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
    if sys.argv[1] == "-h":
        print "Usage: %s nsamples acc_ratio ncpus path_to_module" % sys.argv[0]
        exit(0)
        
    def debug(msg):
        sys.stderr.write(msg)
        sys.stderr.flush()

    nsamples = int(sys.argv[1])
    acc_ratio = float(sys.argv[2])
    ncpus = int(sys.argv[3])
    mod_path = os.path.dirname(sys.argv[4])
    sys.path.append(mod_path)    
    mod = importlib.import_module(os.path.basename(sys.argv[4].replace(".py","")))
    
    # Data in the form of x_hat
    data = mod.example_data()
    h_params = mod.example_h_params()
    sampler = ABCmp(mod.lt_summarize(data), 
                    lambda: mod.lt_prior(h_params), 
                    lambda x: mod.lt_summarize(mod.lt_noisy_obs(mod.lt_model(x,4))), 
                    nworkers=ncpus)
    res = sampler.sample(nsamples,acc_ratio)
    for val in res:
        print mod.lt_format(val)
