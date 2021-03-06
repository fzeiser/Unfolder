
import copy
import ROOT
from Unfolder.Histogram import H1D, H2D
import numpy as np

luminosity = 36.1

'''
Read unfolding factors from a ROOT file
'''
def getHistograms(fname = "out_ttallhad_psrw_Syst.root", direc = "nominal", variable = "mttCoarse"):
  L = luminosity
  f = ROOT.TFile.Open(fname)
  truth = L*H1D(f.Get("%s/%s" % (direc, "unfoldPart_%s" % variable)))
  recoWithFakes = L*H1D(f.Get("%s/%s" % (direc, "unfoldReco_%s_cat2b2HTTmasscut" % variable)))
  # input assumed to have reco in X axis and truth in Y, so transpose it to the truth in X axis convention
  mig = L*H2D(f.Get("%s/%s" % (direc, "unfoldMigRecoPart_%s_cat2b2HTTmasscut" % variable))).T()

  # fakes
  bkg = L*H1D(f.Get("%s/%s" % (direc, "unfoldRecoNotPart_%s_cat2b2HTTmasscut" % variable)))
  #bkg = bkg + other bkgs!!! FIXME

  tr_1dtruth = mig.project('x')
  nrt = truth - tr_1dtruth

  ones = H1D(np.ones(len(nrt.val)))
  ones.err = copy.deepcopy(np.zeros(len(nrt.val)))
  ones.x = copy.deepcopy(nrt.x)
  ones.x_err = copy.deepcopy(nrt.x_err)
  eff = ones + nrt.divideBinomial(truth)*(-1.0)
  #eff = mig.project('x').divideBinomial(truth)

  return [truth, recoWithFakes, bkg, mig, eff, nrt]

