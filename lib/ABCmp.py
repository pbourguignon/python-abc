# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 15:43:00 2014

@author: P.-Y. Bourguignon - pbourguignon@isthmus.fr
"""

import ABC
import multiprocessing
import sys
import datetime

class ABCmp(object):
    def __init__(self, data, f_prior, f_model, f_summarize, nworkers=2):
        self.nworkers = nworkers        
        self.f_summarize, self.f_prior, self.f_model = f_summarize, f_prior, f_model        
        self.data_summary = self.f_summarize(data)
        self.f_distance = self.learn_distance()
        
    def learn_distance(self, size=1000):

        samples = [self.f_summarize(self.f_model(self.f_prior())) \
                    for ii in range(size)]
        w = {}
        for k in self.data_summary.keys():
            component = [s[k] for s in samples]
            ssq = sum([(c-self.data_summary[k])**2 for c in component])
            w[k]=ssq/len(component)
            #sys.stdout.write("Weight "+ str(k)+ ": "+ str(w[k])+"\n")
        return (lambda s: sum([(s[k]-v)**2/w[k] \
                            for k,v in self.data_summary.iteritems()]))
        
    def sample(self, nsamples, acc_ratio):
        queue = multiprocessing.Queue(1000)
        res = multiprocessing.Queue(1000)
        t_high = multiprocessing.Value('f')
        
        samplers = [Sampler(queue, self.f_prior, self.f_model, self.f_summarize) \
                                for ii in range(self.nworkers*2/3)]
        
        evaluators = [Evaluator(queue, res, t_high, self.f_distance) \
                        for ii in range(self.nworkers/3)]
        
        for w in samplers:
            w.start()
        

        ntest = int(10*nsamples * acc_ratio)
        samples = []

        for ii in range(ntest):
            params, summary = queue.get()
            dist = self.f_distance(summary)
            samples.append((params, dist))
        
        min_val = min(samples, key=(lambda x: x[1]))
        thr = min_val[1]
        t_high = max(samples, key=(lambda x: x[1]))[1]
        #print "Queues tuned"
        
        for s in evaluators:
            s.start()
        samples = [[],[]]
        
        for ii in range(nsamples):
            params, dist = res.get()
            if dist < thr:
                samples[0].append((params, dist))
            else:
                samples[1].append((params, dist))
            
            if ii % (nsamples / 100) == 0:
                sys.stderr.write("\rSampling "+ str(ii / (nsamples/100)) + "% completed")
                sys.stderr.flush()
                        
        for w in samplers:
            w.terminate()
        for s in evaluators:
            s.terminate()
        
        res = []
        cur_slice = 0
        ntarget = int(nsamples * acc_ratio)
        while len(res) < ntarget:
            if len(samples[cur_slice]) + len(res) < ntarget:
                res = res + [x[0] for x in samples[cur_slice]]
            else:
                s_slice = sorted(samples[cur_slice], key=lambda x: x[1])
                res = res + [x[0] for x in s_slice[0:ntarget-len(res)]]
        
        return res

    
class Sampler(multiprocessing.Process):
    def __init__(self, queue, f_prior, f_model, f_summarize):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.f_prior, self.f_model, self.f_summarize = f_prior, f_model, f_summarize
    def run(self):
        while True:
            params = self.f_prior()
            obs = self.f_model(params)
            self.queue.put((params, self.f_summarize(obs)))

class Evaluator(multiprocessing.Process):
    def __init__(self, queue, res, t_high, f_distance):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.res = res
        self.t_high = t_high
        self.f_distance = f_distance
    def run(self):
        while True:
            params, summary = self.queue.get()
            dist = self.f_distance(summary)
            if dist < self.t_high:
                self.res.put((params, dist))
            else:
                del params, summary


if __name__ == '__main__':
    nsamples = int(sys.argv[1])
    acc_ratio = float(sys.argv[2])
    ncpus = int(sys.argv[3])
    module = sys.argv[4]
    # Data in the form of x_hat
    data = {'x_hat': [1.05,
                      0.95,1.03,
                      .92,.99,.98,1.03,
                      .98,.91,.95,1.04,1.1,0.99,1.06,.99]}
                      
    h_params = {'mu_x':    (1.25,1.1),
                'sigma_x2':(5, .02),
                'beta_y':  (2.0,10),
                'beta_o':  (2.0,10),}

    sampler = ABCmp(data, lambda: ABC.lt_prior(h_params), lambda x: ABC.lt_noisy_obs(ABC.lt_model(x,4)), ABC.lt_summarize, nworkers=ncpus)
    res = sampler.sample(nsamples,acc_ratio)
    #print res
