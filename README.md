python-abc
==========

A generic implementation of Approximate Bayesian Computation methods, including
a parallel version based on the multiprocessing module.


Basic usage
-----------

The constructor ABC.ABCSampler object takes references to functions:

[f_prior]
generates samples from the prior distribution

[f_model]
takes an output from f_prior, and returns a sample from the model

[f_summarize]
takes an output from f_model, and returns summary statistics



