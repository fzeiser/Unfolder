# Unfolder

This software uses PyMC3 to unfold a distribution, using the Fully Bayesian Unfolding (FBU) method,
proposed in https://arxiv.org/abs/1201.4612.
There is already a software that implements this in https://github.com/gerbaudo/fbu , but it uses PyMC2.
The current software aims to extend it to PyMC3, so that one can use more efficient sampling techniques, such as
HMC and NUTS.

More information on FBU can be found in https://arxiv.org/abs/1201.4612

More information about PyMC3 can be found in https://peerj.com/articles/cs-55/ and https://pymc-devs.github.io/pymc3/notebooks/getting_started.html. Its GitHub project is in: https://github.com/pymc-devs/pymc3

More information on NUTS can be found in http://www.jmlr.org/papers/volume15/hoffman14a/hoffman14a.pdf

More information on HMC can be found in http://www.sciencedirect.com/science/article/pii/037026938791197X?via%3Dihub


# Installing pre-requisites

You can use install Numpy, Matplotlib, SciPy, Pandas, Seaborn and pyMC3 in Ubuntu as follows.

```
sudo apt-get install python-pip python-dev build-essential python-matplotlib python-numpy python-scipy
pip install pandas
pip install seaborn
pip install pymc3
```

After this, running the following should run a test unfolding:

```
./test.py
```


# Usage

Given a background histogram to be subtracted ```bkg```; a matrix ```mig``` with counts in its element ```mig[i, j]```
how many events are expected to have been renerated in particle-level bin ```i``` and reconstructed-level bin ```j```;
and an efficiency histogram ```eff```, which has in each entry ```i```
(1 - (# events in truth bin ```i``` that fails reconstruction)/(# events in truth bin ```i```));
we can build the unfolding model as follows:

```
model = Unfolder(bkg, mig, eff)     # Call the constructor to initialise the model parameters
model.setUniformPrior()             # Using a uniform prior is the default
#model.setGaussianPrior()           # For a Gaussian prior with means at the truth bins
                                    # and width in each bin given by sqrt(truth)
#model.setGaussianPrior(mean, sd)   # If vectors (with the size of the truth distribution number of bins)
                                    # are given, they will be used as the means and widths of the Gaussians
                                    # bin-by-bin, instead of the defaults
```

The response matrix P(reco = j|truth = i)*efficiency(i) is now stored in ```model.response```.
For convenience, the same matrix without the efficiency multiplication is stored in ```model.response_noeff```.

The statistical model can be prepared for a given input data as follows:

```
model.run(data)
```

Afterwards, one can draw samples to find the posterior as follows:

```
model.sample(20000)
```

The toy ```k``` produced in the trith bin ```i``` are stored in ```model.trace.Truth[k, i]```. So you can see
the distribution of the posterior marginalized for bin ```i``` by plotting:

```
plt.figure()
sns.distplot(model.trace.Truth[:, i], kde = True, hist = True, label = "Posterior histogram marginalized in bin %d" %i)
plt.legend()
plt.show()
```

If you are only interested in the means of the posterior marginalized in each bin, you can plot it to compare it with
the truth distribution as follows:

```
model.plotUnfolded(x, x_err, "plotUnfolded.png")
```

Here, ```x``` are the X axis entries for the plot and ```x_err``` are the half-width of the X axis bins for cosmetic
reasons.


