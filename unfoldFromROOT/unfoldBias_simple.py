#!/usr/bin/env python

import itertools
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns 
import numpy as np
import pymc3 as pm
import matplotlib.cm as cm
import scipy

from Unfolder.ComparisonHelpers import *
from Unfolder.Unfolder import Unfolder
from Unfolder.Histogram import H1D, H2D, plotH1D, plotH2D
from readHistograms import *

sns.set(context = "paper", style = "whitegrid", font_scale=2)

varname = "observable"
extension = "eps"

# get histograms from file
truth = {}
recoWithFakes = {}
recoWithoutFakes = {}
bkg = {}
mig = {}
eff = {}
nrt = {}

truth["A"], recoWithFakes["A"], bkg["A"], mig["A"], eff["A"], nrt["A"] = getHistograms("out_ttallhad_psrw_Syst.root", "nominal", "mttAsymm")
truth["B"], recoWithFakes["B"], bkg["B"], mig["B"], eff["B"], nrt["B"] = getHistograms("out_ttallhad_psrw_Syst.root", "aMcAtNloHerwigppEvtGen", "mttAsymm")
truth["C"], recoWithFakes["C"], bkg["C"], mig["C"], eff["C"], nrt["C"] = getHistograms("out_ttallhad_psrw_Syst.root", "PowhegHerwigppEvtGen", "mttAsymm")

for i in recoWithFakes:
  recoWithoutFakes[i] = mig[i].project("y")

  # plot migration matrix as it will be used next for unfolding
  plotH2D(mig[i].T(), "Particle-level bin", "Reconstructed-level bin", "Number of events for each (reco, truth) configuration", "mig_%s.%s" % (i,extension))

  # plot 1D histograms for cross checks
  plotH1D(bkg[i], "Reconstructed "+varname, "Events", "Background", "bkg_%s.%s" % (i, extension))
  plotH1D(truth[i], "Particle-level "+varname, "Events", "Particle-level distribution", "truth_%s.%s" % (i, extension))
  plotH1D(nrt[i], "Particle-level "+varname, "Events", "Events in particle-level selection but not reconstructed", "nrt_%s.%s" % (i,extension))
  plotH1D(recoWithFakes[i], "Reconstructed "+varname, "Events", "Reconstructed-level distribution with fakes", "recoWithFakes_%s.%s" % (i,extension))
  plotH1D(recoWithoutFakes[i], "Reconstructed "+varname, "Events", "Reconstructed-level distribution without fakes", "recoWithoutFakes_%s.%s" % (i,extension))
  plotH1D(eff[i], "Particle-level "+varname, "Efficiency", "Efficiency of particle-level selection", "eff_%s.%s" % (i,extension))

# generate perfect fake data
data = recoWithFakes[""]

# generate fake data from model
pseudo_data = getDataFromModel(bkg[""], mig[""], eff[""])

comparePlot([data, pseudo_data, data - bkg[""], pseudo_data - bkg[""]],
            ["Reco. projected from unfolding factors", "Reco. simulated with toy experiments",
             "Reco. projected from unfolding factors - bkg", "Reco. simulated with toy experiments - bkg"],
            luminosity*1e-3, True, "fb/GeV", "pseudoData.%s" % extension)

# Create unfolding class
m = Unfolder(bkg[""], mig[""], eff[""], truth[""])
m.setUniformPrior()
#m.setGaussianPrior()
#m.setCurvaturePrior()
#m.setEntropyPrior()
#m.setFirstDerivativePrior()

# add uncertainties
uncList = [] #'sjcalib1030', 'eup', 'ecup'] + ['lup'+str(x) for x in range(0, 10+1)] + ['cup'+str(x) for x in range(0, 3+1)] + ['bup'+str(x) for x in range(0, 3+1)] + ['ewkup']
for k in uncList:
  print "Getting histograms for syst. ", k
  struth, srecoWithFakes, sbkg, smig, seff, snrt = getHistograms("out_ttallhad_psrw_Syst.root", k, "mttAsymm")
  m.addUncertainty(k, sbkg, smig.project('y'))
  plotH1D(m.bkg_syst[k], "Reconstructed "+varname, "Events", "Background Uncertainty "+k, "bkg_unc_%s.%s" % (k, extension))
  plotH1D(m.reco_syst[k], "Reconstructed "+varname, "Events", "Impact in reconstructed distribution due to uncertainty "+k, "recoWithoutFakes_unc_%s.%s" % (k, extension))
  

# plot response matrix P(r|t)*eff(r)
plotH2D(m.response.T(), "Particle-level bin", "Reconstructed-level bin", "Response matrix P(r|t)*eff(t)", "responseMatrix.%s" % extension)
# and also the migration probabilities matrix
plotH2D(m.response_noeff.T(), "Particle-level bin", "Reconstructed-level bin", "Migration probabilities P(r|t)", "migrationMatrix.%s" % extension)

# the following does the same as before, but
# it is used for double checking that the unfolding class reads the info. properly
#plotH1D(m.truth, "Particle-level "+varname, "Events", "Particle-level distribution estimated from migrations", "truth_crossCheck.%s" % extension)
#plotH1D(m.eff, "Particle-level "+varname, "Efficiency", "Efficiency of particle-level selection in unfolder", "eff_crossCheck.%s" % extension)
#plotH2D(m.mig.T(), "Particle-level bin", "Reconstructed-level bin", "Number of events for each (reco, truth) configuration", "mig_crossCheck.%s" % extension)
#plotH1D(m.bkg, "Reconstructed "+varname, "Events", "Background (including fakes)", "bkg_crossCheck.%s" % extension)
#plotH1D(m.recoWithoutFakes, "Reconstructed "+varname, "Events", "Reconstructed-level distribution", "recoWithoutFakes_crossCheck.%s" % extension)

# add migration uncertainty
#uncUnfList = ["B", "C"]
#for k in uncUnfList:
#  m.addUnfoldingUncertainty(k, bkg[k], mig[k], eff[k])

# try a curvature-based prior
# first choose alpha using only a MAP estimate
#m.setEntropyPrior()
#m.setCurvaturePrior()
m.setFirstDerivativePrior(1.0)
#m.setGaussianPrior()

#m.setConstrainArea(True)
m.run(data)
# does the same for the pseudo-data

alpha = {}
alphaChi2 = {}
bestAlphaBias = {}
bestAlphaBiasStd = {}
bestAlphaNormBias = {}
bestAlphaNormBiasStd = {}

for i in ["A", "B", "C"]:
  print "Checking bias due to configuration '%s'" % i

  alpha[i] = -1
  alphaChi2[i] = -1
  bestAlphaBias[i] = -1
  bestAlphaBiasStd[i] = -1
  bestAlphaNormBias[i] = -1
  bestAlphaNormBiasStd[i] = -1

  # for first deriv:
  t_bkg = bkg[i]
  t_mig = mig[i]
  t_eff = eff[i]
  alpha[i], alphaChi2[i], bestAlphaBias[i], bestAlphaBiasStd[i], bestAlphaNormBias[i], bestAlphaNormBiasStd[i] = m.scanAlpha(t_bkg, t_mig, t_eff, 1000, np.arange(0.0, 5.0, 0.250), "scanAlpha_%s.%s" % (i, extension), "scanAlpha_%s_chi2.%s" % (i, extension), "scanAlpha_%s_norm.%s" % (i, extension))
  # for curvature
  #alpha[i], alphaChi2[i], bestAlphaBias[i], bestAlphaBiasStd[i], bestAlphaNormBias[i], bestAlphaNormBiasStd[i] = m.scanAlpha(t_bkg, t_mig, t_eff, 1000, np.arange(0.0, 4e-8, 2e-9), "scanAlpha_%s.%s" % (i, extension), "scanAlpha_%s_chi2.%s" % (i, extension), "scanAlpha_%s_norm.%s" % (i, extension))
  # for entropy
  #alpha[i], alphaChi2[i], bestAlphaBias[i], bestAlphaBiasStd[i], bestAlphaNormBias[i], bestAlphaNormBiasStd[i] = m.scanAlpha(t_bkg, t_mig, t_eff, 1000, np.arange(0.0, 100.0, 4.0), "scanAlpha_%s.%s" % (i, extension), "scanAlpha_%s_chi2.%s" % (i, extension), "scanAlpha_%s_norm.%s" % (i, extension))
  print "For configuration '%s': Found alpha = %f with bias chi2 = %f, bias mean = %f, bias std = %f, norm bias = %f, norm bias std = %f" % (i, alpha[i], alphaChi2[i], bestAlphaBias[i], bestAlphaBiasStd[i], bestAlphaNormBias[i], bestAlphaNormBiasStd[i])

# do the rest with the best alpha from stat. test only
m.setAlpha(alpha["A"])

m.run(pseudo_data)
m.setData(pseudo_data)
m.sample(100000)

# plot marginal distributions
m.plotMarginal("plotMarginal_pseudo.%s" % extension)
for i in uncList:
  m.plotNPMarginal(i, "plotNPMarginal_pseudo_%s.%s" % (i, extension))

# plot unfolded spectrum
m.plotUnfolded("plotUnfolded_pseudo.%s" % extension)
m.plotOnlyUnfolded(luminosity*1e-3, True, "fb/GeV", "plotOnlyUnfolded_pseudo.%s" % extension)

# plot correlations graphically
# it takes forever and it is just pretty
# do it only if you really want to see it
# I just get annoyed waiting for it ...
#m.plotPairs("pairPlot.%s" % extension) # takes forever!

suf = "_pseudo"
m.plotCov("covPlot%s.%s" % (suf, extension))
m.plotCorr("corrPlot%s.%s" % (suf, extension))
m.plotCorrWithNP("corrPlotWithNP%s.%s" % (suf, extension))
m.plotSkewness("skewPlot%s.%s" % (suf, extension))
m.plotKurtosis("kurtosisPlot%s.%s" % (suf, extension))
m.plotNP("plotNP%s.%s" % (suf, extension))

# for debugging
#print "Mean of unfolded data:"
#print np.mean(m.trace.Truth, axis = 0)
#print "Sqrt of variance of unfolded data:"
#print np.std(m.trace.Truth, axis = 0)
#print "Skewness of unfolded data:"
#print scipy.stats.skew(m.trace.Truth, bias = False)
#print "Kurtosis of unfolded data:"
#print scipy.stats.kurtosis(m.trace.Truth, bias = False)
#print "Print out of the covariance matrix follows:"
#print np.cov(m.trace.Truth, rowvar = False)

m.plotUnfolded("plotUnfolded_pseudo.%s" % extension)
m.plotOnlyUnfolded(luminosity*1e-3, True, "fb/GeV", "plotOnlyUnfolded_pseudo.%s" % extension)

pseudo_fbu_result = m.hunf

# keep alpha and prior, but now unfold the original distribution
m.run(data)
m.setData(data)
m.sample(100000)

# plot marginal distributions
m.plotMarginal("plotMarginal.%s" % extension)
for i in uncList:
  m.plotNPMarginal(i, "plotNPMarginal_%s.%s" % (i, extension))

m.plotUnfolded("plotUnfolded.%s" % extension)
m.plotOnlyUnfolded(luminosity*1e-3, True, "fb/GeV", "plotOnlyUnfolded.%s" % extension)

suf = ""
m.plotCov("covPlot%s.%s" % (suf, extension))
m.plotCorr("corrPlot%s.%s" % (suf, extension))
m.plotCorrWithNP("corrPlotWithNP%s.%s" % (suf, extension))
m.plotSkewness("skewPlot%s.%s" % (suf, extension))
m.plotKurtosis("kurtosisPlot%s.%s" % (suf, extension))
m.plotNP("plotNP%s.%s" % (suf, extension))

fbu_result = m.hunf

comparePlot([truth[""],
             fbu_result,
             pseudo_fbu_result],
            ["Particle-level",
             "Unfolded (FBU) from projected reco.",
             "Unfolded (FBU) from independently simulated reco.",
            ],
            luminosity*1e-3, True, "fb/GeV", "biasTest.%s" % extension)

print "FBU     -- alpha = ",     alpha, " with bias = ", bestAlphaBias, ", std = ", bestAlphaBiasStd, ", norm bias = ", bestAlphaNormBias, ", norm bias std = ", bestAlphaNormBiasStd

