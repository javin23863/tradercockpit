---
title: Monte Carlo simulation count — academic ontology receipt
type: research
status: reviewed
reviewed: 2026-07-29
scope: teaching-series terminology and claims
---

# Monte Carlo simulation count — academic ontology receipt

## Editorial ruling

**REJECT:** “Monte Carlo simulations should not exceed 200.”

There is no general academic ceiling at 200. The likely source is a category error from Efron
and Tibshirani’s 1993 guidance: they said more than 200 **bootstrap replications for estimating
a standard error** were seldom needed in their examples. They did not say that more simulations
are harmful, and they explicitly required larger counts for bootstrap confidence intervals.

The repository wording found during this review is narrower but still unsupported as a general
standard:

> “Monte Carlo parameter perturbation — two hundred simulations per candidate.”
>
> Source: `productions/video-01/vo.txt:30`

That sentence can describe an implementation budget only after the target statistic and its
measured Monte Carlo error are supplied. It must not be taught as a mathematical optimum,
maximum, or proof of robustness.

## Approved beginner wording

> There is no magic maximum such as 200 Monte Carlo runs. For independent paths, more paths make
> the estimate steadier, but the improvement is slow: four times as many paths cuts the
> simulation’s sampling error roughly in half. We choose the count from the precision we need and
> report the uncertainty that remains. Two hundred may be enough to demonstrate the idea or to
> estimate a rough standard error in some bootstrap problems, but it can be far too small for
> confidence intervals or rare-loss tails.

Short version:

> More runs make the simulation steadier, not truer. We stop when the simulation error is small
> enough for the decision, not when a universal counter reaches 200.

## Ontology records

### `mc-count-001` — no universal simulation count

- **claim:** The number of independent Monte Carlo replications should be chosen from the target
  quantity and acceptable Monte Carlo error; no single count is suitable across simulation
  settings.
- **scope:** Simulation studies made from independent complete replications.
- **assumptions:** Every replication follows the same declared design and is independent of the
  others.
- **source_url:** https://pmc.ncbi.nlm.nih.gov/articles/PMC3337209/
- **doi:** https://doi.org/10.1198/tast.2009.0030
- **locator:** Koehler, Brown, and Haneuse (2009), §2.1, p. 156, equation (1); discussion after
  Table 1 in §3; §4.1, pp. 159–160, equations (6)–(7); §6, pp. 161–162.
- **limitations:** Monte Carlo error is uncertainty caused by a finite replication count. It is
  separate from historical-sample uncertainty, measurement error, and model risk.
- **status:** verified_primary

### `mc-count-002` — square-root convergence

- **claim:** For an IID sample-mean estimator with finite variance,
  `Var(mean) = sigma^2 / n` and `RMSE = sigma / sqrt(n)`. Four times as many independent
  replications halves the typical Monte Carlo error.
- **scope:** Independent simulated outcomes or path-level summaries averaged to estimate an
  expectation.
- **assumptions:** IID draws, finite variance, a correctly implemented generator, and the sample
  mean as estimator.
- **source_url:** https://artowen.su.domains/mc/Ch-intro.pdf
- **doi:** null
- **locator:** Art Owen, *Monte Carlo Theory, Methods and Examples*, Chapter 2, §2.1,
  pp. 16–18, especially equation (2.5); §2.2, pp. 18–20, especially equation (2.14).
- **limitations:** The result does not cover correlated draws, infinite-variance cases, every
  quantile estimator, or model misspecification. More valid draws reduce simulation noise
  conditional on the model; they do not make a bad model true.
- **status:** verified_primary

### `mc-count-003` — what the historical “200” actually meant

- **claim:** Efron and Tibshirani’s “more than 200 is seldom needed” statement applies to
  bootstrap replications used to estimate a standard error. It is a task-specific rule of thumb,
  not a maximum for Monte Carlo paths, confidence intervals, tail estimates, or trading tests.
- **scope:** Nonparametric bootstrap standard-error estimation.
- **assumptions:** The empirical distribution is an appropriate population stand-in and the
  resampling design matches the data’s dependence structure.
- **source_url:** https://doi.org/10.1007/978-1-4899-4541-9
- **doi:** https://doi.org/10.1007/978-1-4899-4541-9
- **locator:** Efron and Tibshirani, *An Introduction to the Bootstrap*, Chapter 6:
  Algorithm 6.1 and equation (6.7), pp. 47–48; §6.4, pp. 50–52, especially equation (6.9)
  and the two rules of thumb on p. 52. The same page says much larger `B` is required for
  bootstrap confidence intervals; p. 69 reports that 200 replications did not reveal a
  distribution’s shape clearly.
- **limitations:** Published in 1993 under much higher computation costs. “Seldom needed” is not a
  theorem and does not say additional valid resamples degrade an estimator.
- **status:** verified_primary

### `mc-count-004` — later bootstrap guidance

- **claim:** For bootstrap and permutation work, 200 is below later accuracy-oriented guidance:
  1,000 resamples can be adequate for rough approximations, 10,000 is recommended for routine
  use, and about 15,000 is required in the paper’s worked 2.5% tail example to keep Monte Carlo
  variation within 10% of the target with 95% probability.
- **scope:** Bootstrap confidence intervals and permutation-test tail probabilities, not every
  Monte Carlo application.
- **assumptions:** The paper’s resampling model and its stated 95% probability / 10% relative-error
  criterion.
- **source_url:** https://www.amstat.org/docs/default-source/amstat-documents/edu-resamplingundergradcurriculum.pdf
- **doi:** https://doi.org/10.1080/00031305.2015.1089789
- **locator:** Hesterberg (2015), §3.6, pp. 27–30: p. 27 identifies the older `r=200`
  guidance; pp. 28–29 derive `r >= 14,982`; pp. 29–30 recommend 10,000 for routine use
  and more when accuracy matters.
- **limitations:** These are recommendations for the specified resampling tasks and accuracy
  target, not a universal minimum for all simulations.
- **status:** verified_primary

### `mc-count-005` — 200 paths and probability estimates

- **claim:** If an event has probability `p` and is counted across `n` independent paths, the
  estimated proportion has Monte Carlo standard error `sqrt(p(1-p)/n)`. At `n=200`, a 5% event
  appears 10 times on average and has MCSE about 1.54 percentage points (about 31% of the target);
  a 1% event appears twice on average and has MCSE about 0.70 percentage points (about 70% of the
  target).
- **scope:** Event probabilities estimated from independent Bernoulli path indicators.
- **assumptions:** Independent paths, a fixed event definition, and a correct data-generating
  model. Arithmetic is derived directly from the cited binomial formula.
- **source_url:** https://artowen.su.domains/mc/Ch-intro.pdf
- **doi:** null
- **locator:** Owen, Chapter 2, §2.4, pp. 23–25, especially equations (2.21)–(2.23) and the
  rare-event discussion.
- **limitations:** Normal approximations are unreliable near a boundary with very few events;
  exact binomial intervals are preferable. Quantile accuracy also depends on density near the
  target quantile. More paths cannot repair an unrealistic tail model.
- **status:** verified_primary_derived_arithmetic

### `mc-count-006` — 200 can be illustrative without being inferential

- **claim:** A small resampling count can be useful for teaching because viewers can watch a
  sampling distribution build, but a visual demonstration is not evidence that its estimated
  tails or decision thresholds are precise.
- **scope:** Teaching visuals and classroom demonstrations.
- **assumptions:** The visual is labeled as illustrative and no research-grade numerical claim is
  inferred from the displayed count.
- **source_url:** https://www.amstat.org/docs/default-source/amstat-documents/edu-resamplingundergradcurriculum.pdf
- **doi:** https://doi.org/10.1080/00031305.2015.1089789
- **locator:** Hesterberg (2015), §2.5–2.6, pp. 12–13, recommends making sampling distributions
  concrete and starting with small hand-worked samples; §3.6, pp. 27–30, separately treats
  production accuracy.
- **limitations:** The source does not ratify 200 as a special visual count. “200 may be
  illustrative” is an editorial use boundary, not a precision claim.
- **status:** verified_primary_editorial_application

### `mc-term-001` — simulated path

- **claim:** A simulated path is one complete trajectory through time. If each path is generated
  independently and one target summary is calculated from each path, the number of paths is also
  the number of independent Monte Carlo replications for that summary.
- **scope:** Path-based financial simulation.
- **assumptions:** Independent path generation and one path-level observation per target statistic.
- **source_url:** https://www.federalreserve.gov/pubs/feds/2008/200821/200821pap.pdf
- **doi:** https://doi.org/10.1287/mnsc.1100.1213
- **locator:** Gordy and Juneja, §2 “Simulation framework,” pp. 4–5: each outer trial draws one
  path to the horizon and produces one loss observation.
- **limitations:** Multiple correlated paths, reused random numbers, or multiple observations
  taken from one path require a different effective-sample calculation.
- **status:** verified_primary

### `mc-term-002` — complete replication

- **claim:** One simulation-study replication repeats the full data generation, analysis
  procedure, and recorded result. It is not merely one arithmetic step inside the procedure.
- **scope:** Statistical simulation studies.
- **assumptions:** The study design specifies what is regenerated and what remains fixed.
- **source_url:** https://pmc.ncbi.nlm.nih.gov/articles/PMC3337209/
- **doi:** https://doi.org/10.1198/tast.2009.0030
- **locator:** Koehler, Brown, and Haneuse, §1 and §2: the three-step simulation-study definition
  and notation `{X_1, X_2, ...}` for independent replicates.
- **limitations:** A software log may use “run” or “iteration” differently; the script must define
  the unit before giving a count.
- **status:** verified_primary

### `mc-term-003` — bootstrap resample

- **claim:** One nonparametric bootstrap replication draws a sample of size `n`, with replacement,
  from the observed sample and computes the statistic once. The replication count `B` is distinct
  from the original sample size `n`.
- **scope:** Ordinary nonparametric bootstrap.
- **assumptions:** IID-style empirical resampling is appropriate; dependent data need a
  dependence-aware bootstrap.
- **source_url:** https://doi.org/10.1007/978-1-4899-4541-9
- **doi:** https://doi.org/10.1007/978-1-4899-4541-9
- **locator:** Efron and Tibshirani, Chapter 6, Algorithm 6.1, pp. 47–48.
- **limitations:** This definition does not validate naive individual-trade or individual-day
  resampling when observations are serially dependent.
- **status:** verified_primary

### `mc-term-004` — MCMC iteration and effective sample size

- **claim:** An MCMC iteration is not necessarily an independent simulation. Correlation means raw
  iterations must be translated into effective sample size; MCSE scales as
  `1/sqrt(N_eff)`, not automatically as `1/sqrt(raw iterations)`.
- **scope:** Markov chain Monte Carlo.
- **assumptions:** The chain has reached its target distribution, required moments exist, and
  autocorrelation can be estimated.
- **source_url:** https://mc-stan.org/docs/reference-manual/analysis.html#effective-sample-size
- **doi:** null
- **locator:** Stan Reference Manual 2.39, “Posterior Analysis” → “Markov chains,”
  “Effective sample size,” “Definition of effective sample size,” and “Estimation of MCMC
  standard error”; especially the `N_eff` autocorrelation formula.
- **limitations:** Effective sample size is parameter- and estimand-specific. A large raw iteration
  count does not prove convergence.
- **status:** verified_official

### `mc-term-005` — batch

- **claim:** In simulation output analysis, a batch is a contiguous group of iterations used to
  estimate long-run variance or Monte Carlo error. It is not another name for a path,
  replication, or iteration.
- **scope:** Dependent steady-state or MCMC simulation output.
- **assumptions:** The stationarity, ergodicity, moment, and batch-growth conditions required by
  the selected batch-means estimator.
- **source_url:** https://arxiv.org/abs/0811.1729
- **doi:** https://doi.org/10.1214/09-AOS735
- **locator:** Flegal and Jones (2010), §3 “Batch means,” especially equation (6), pp. 1041–1042;
  output from `n = a_n b_n` iterations is divided into `a_n` batches of length `b_n`.
- **limitations:** Too-short correlated batches understate uncertainty. Changing the number or
  size of batches without increasing total information is not equivalent to generating more
  independent paths.
- **status:** verified_primary

### `mc-term-006` — nested outer and inner trials

- **claim:** Nested simulation has two counts: an outer trial draws a market-risk path to the
  horizon; inner trials reprice instruments conditional on that outer state. The two counts solve
  different problems and must not be collapsed into a single “number of simulations.”
- **scope:** Nested portfolio-risk simulation.
- **assumptions:** Conditional repricing, the paper’s regularity conditions, and its computational
  cost model.
- **source_url:** https://www.federalreserve.gov/pubs/feds/2008/200821/200821pap.pdf
- **doi:** https://doi.org/10.1287/mnsc.1100.1213
- **locator:** Gordy and Juneja, §2 “Simulation framework,” including `L` outer trials and `N_k`
  inner trials; §2.2 budget allocation; §3 Figures 3–5.
- **limitations:** The paper’s finding that relatively few inner trials can suffice in some
  portfolio settings cannot be generalized into a small total-path rule.
- **status:** verified_primary

### `mc-design-001` — dependence-aware resampling

- **claim:** Resampling a market time series must account for temporal dependence when that
  dependence matters. Increasing the number of incorrectly constructed IID resamples does not
  repair the invalid resampling design.
- **scope:** Weakly dependent stationary observations.
- **assumptions:** The stationarity and weak-dependence conditions of the chosen block-bootstrap
  method.
- **source_url:** https://doi.org/10.1080/01621459.1994.10476870
- **doi:** https://doi.org/10.1080/01621459.1994.10476870
- **locator:** Politis and Romano (1994), abstract and §§1–2, pp. 1303–1307: the stationary
  bootstrap resamples blocks of random length to preserve dependence in a stationary pseudo-time
  series.
- **limitations:** A stationary bootstrap does not solve structural breaks, changing regimes, or
  nonstationarity. Those are model-design questions, not replication-count questions.
- **status:** verified_primary

### `mc-design-002` — precision does not establish truth

- **claim:** More valid resamples reduce implementation variability but do not fundamentally
  change the center, spread, or shape of the theoretical bootstrap distribution being
  approximated. More simulation can therefore produce a precise answer to a misspecified
  question.
- **scope:** Monte Carlo approximation of a fixed bootstrap distribution; the final sentence is
  the corresponding editorial implication.
- **assumptions:** The resampling design and original data are held fixed while replication count
  increases.
- **source_url:** https://www.amstat.org/docs/default-source/amstat-documents/edu-resamplingundergradcurriculum.pdf
- **doi:** https://doi.org/10.1080/00031305.2015.1089789
- **locator:** Hesterberg (2015), §3.1, p. 21, and §3.6, pp. 27–30.
- **limitations:** Better resampling design, variance reduction, new independent data, or a revised
  model can change the target distribution; merely raising the count cannot.
- **status:** verified_primary_editorial_implication

## Required production receipt before stating a count

Any future script that names a Monte Carlo count should have all of these fields in its private
fact pack:

1. `unit`: path, complete replication, bootstrap resample, MCMC iteration, batch, outer trial, or
   inner trial;
2. `estimand`: mean, probability, quantile, drawdown, confidence endpoint, pass rate, or another
   named statistic;
3. `dependence_model`: IID, block/stationary bootstrap, Markov chain, or another declared model;
4. `count`;
5. `mcse_or_interval`: measured Monte Carlo standard error or confidence interval for the
   reported statistic;
6. `stopping_rule`: the tolerance that made the count sufficient;
7. `seed_policy`: fixed seeds for reproducibility plus independent-seed stability check;
8. `limitations`: what the simulation does not test, especially model misspecification,
   selection overfitting, nonstationarity, and unseen data.

No count receipt means no count in the spoken track.
