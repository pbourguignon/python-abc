python-abc
==========

A generic implementation of Approximate Bayesian Computation methods, including
a parallel version based on the multiprocessing module.


Basic usage
-----------

A frontend to the sampler is provided. All you need to provide is a python module exposing functions:

* *prior(hparams)*
	return a sample @params@ from the prior

* *statistics(params)*
	return a sample of the statistics (should be a dictionary, like @{'avg': 1.02, 'std': 0.201}@


Library usage
-------------

The sampler comes in two flavor: a non-parallel version (in module ABC.py), mostly meant
for educational purposes,  and a parallel version (in module ABCmp.py). Both interfaces are mostly identical.

The main class is ABC.ABCSampler (ABCmp.ABCmp respectively). Its constructor takes references to the functions 
@prior@ and @statistisc@ above. Optionally, a custom distance function can also be used.

If these functions are available from a single module *user_module*, then a
simple code like would do the job:

    from user_module import some_function as f_prior
    from user_module import some_other_function as f_model
    from user_module import yet_another_function as f_summarize
    import ABC

    # Load your data
    data = ...

    abc = ABC.ABCSampler( data, 
                          user_module.f_prior, 
                          user_module.f_model,
                          user_module.f_summarize)
    
    res = abc.sample(nsamples, acc_ratio)

