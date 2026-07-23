# Deep research: engineering (verified claims; synthesis interrupted by usage limit)

*Confirmed claims below survived 3-vote adversarial verification. Unverified claims from this run are NOT included and must not be quoted.*

- **Shallow architectures beat deep ones for cross-sectional return prediction: neural network performance peaks at three hidden layers and declines with more layers, and boosted-tree/random-forest algorithms select trees averaging fewer than six leaves — attributed to small data and a tiny signal-to-noise ratio relative to domains where deep learning thrives.**
  Source: https://dachxiu.chicagobooth.edu/download/ML.pdf | vote 3-0

- **Small predictive R² translates into large portfolio economics: a value-weighted long-short decile spread sorted on neural-network forecasts earns an annualized out-of-sample Sharpe ratio of 1.35 (2.45 equal-weighted), versus 0.61 and 0.83 for the same strategy built on benchmark OLS forecasts.**
  Source: https://dachxiu.chicagobooth.edu/download/ML.pdf | vote 3-0

- **Their validation scheme sets a documented precedent for retraining cadence and hyperparameter honesty: models are refit only once per year (not monthly) on an expanding training window with a rolling 12-year validation sample used for tuning, and they explicitly avoid k-fold cross-validation to preserve temporal ordering of the data.**
  Source: https://dachxiu.chicagobooth.edu/download/ML.pdf | vote 3-0

- **The tree-vs-deep-net comparison is based on a systematic benchmark of 45 tabular datasets with a large tuning budget per method, making the result robust to hyperparameter-search effort rather than an artifact of under-tuned neural nets.**
  Source: https://arxiv.org/abs/2207.08815 | vote 3-0

- **In a large-scale evaluation across 46 public tabular datasets, attention-based (transformer-style) and retrieval-based deep learning architectures do not convincingly outperform simple MLP baselines, undermining the case for transformers on tabular characteristic-panel-style data.**
  Source: https://arxiv.org/pdf/2410.24210 | vote 3-0

- **TabM, a parameter-efficient ensemble of MLPs, matches gradient-boosted decision trees (XGBoost/LightGBM/CatBoost) on tabular benchmarks rather than beating them — i.e., as of this ICLR 2025 paper, GBDT remains at least on par with the best practical tabular deep learning models.**
  Source: https://arxiv.org/pdf/2410.24210 | vote 3-0

- **The GAN-based no-arbitrage SDF model achieves an annual out-of-sample Sharpe ratio of 2.6, versus 1.7 for its linear special case, 1.5 for a pure deep-learning return-forecasting approach (Gu-Kelly-Xiu style), and 0.8 for the Fama-French five-factor model.**
  Source: https://arxiv.org/pdf/1904.00745 | vote 3-0

- **Off-the-shelf deep-learning prediction methods applied directly to stock returns can underperform even linear models that impose no-arbitrage structure; economic constraints in the learning algorithm are the key to detecting the low signal-to-noise risk-premium signal.**
  Source: https://arxiv.org/pdf/1904.00745 | vote 3-0

- **Deep networks' advantage over linear/additive models comes almost entirely from interaction effects between characteristics, not from univariate nonlinearity — individually, most characteristics affect the SDF approximately linearly.**
  Source: https://arxiv.org/pdf/1904.00745 | vote 3-0

- **On MSCI Japan constituents (roughly 320-340 large/mid-cap stocks) using 25 standard cross-sectional factors at 5 lagged time points, deep feedforward networks with more layers achieved higher out-of-sample rank correlation than shallow 3-layer networks: the best 8-layer DNN reached Spearman rank correlation 0.0591 vs 0.0437 for the worst 3-layer net, and the deep nets beat 3-layer nets even when the shallow nets' parameter counts were matched to the deep ones.**
  Source: https://arxiv.org/pdf/1801.01777 | vote 3-0

- **The deep nets' edge over tree ensembles was marginal, not decisive: the best random forest (max_features=25, max_depth=7, 1000 trees) achieved rank correlation 0.0576 vs 0.0591 for the best DNN, and the authors explicitly state DNN shows little superiority to RF and that their results cannot establish DNN superiority — evidence that on characteristic-panel tabular data, tree ensembles remain competitive with deep nets.**
  Source: https://arxiv.org/pdf/1801.01777 | vote 3-0

