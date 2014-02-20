# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 14:13:07 2014

@author: P.-Y. Bourguignon - bourguig@mis.mpg.de

A simple generic ABC sampler
"""
import sys


class ABCSampler(object):
    def __init__(self, data,
                 f_prior, f_model,
                 f_summarize):
        self.f_prior, self.f_model, self.f_summarize = f_prior, f_model, f_summarize
        self.data_summary = f_summarize(data)        
        #print "Data summary", self.data_summary
        self.f_distance = self.learn_distance()
        
    def sample(self, size, acc_ratio):
        """
        Parameters
        ----------
        size        the number of samples to generate before filtering
        acc_ratio   the ratio of "best" samples to be kept
        """
        samples = []
        for ii in range(size):
            params = self.f_prior()
            obs = self.f_model(params)
            samples.append((params, self.f_distance(self.f_summarize(obs))))
            if ii % (size / 100) == 0:
                sys.stderr.write("\rSampling "+ str(ii / (size/100)) + "% completed")
                sys.stderr.flush()
        s_samples = sorted(samples, key=(lambda x: x[1]))
        return [x[0] for x in s_samples[0:int(size*acc_ratio)]]
            
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
        




