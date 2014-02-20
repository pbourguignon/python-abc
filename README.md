python-abc
==========

A generic implementation of Approximate Bayesian Computation methods, including
a parallel version based on the multiprocessing module.


Basic usage
-----------

The sampler comes in two flavor: a non-parallel version (in module ABC.py) and
a parallel version (in module ABCmp.py). Both interfaces are mostly identical.

The main class is ABC.ABCSampler (ABCmp.ABCmp respectively). Its constructor takes references to functions:

* @f_prior@ generates samples from the prior distribution

* @f_model@ takes an output from f_prior, and returns a sample from the model

* @f_summarize@ takes an output from f_model, and returns summary statistics



