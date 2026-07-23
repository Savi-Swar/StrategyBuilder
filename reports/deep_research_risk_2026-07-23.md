# Deep research: risk (verified claims; synthesis interrupted by usage limit)

*Confirmed claims below survived 3-vote adversarial verification. Unverified claims from this run are NOT included and must not be quoted.*

- **For a single stock modeled as geometric Brownian motion, the optimal Kelly fraction is f = mu/sigma^2, where mu is the growth rate and sigma the relative volatility; the paper reproduces this as the small-mu, small-sigma limit of its exact expression f = (e^mu - 1)/(1 + e^(2mu+sigma^2) - 2e^mu).**
  Source: https://arxiv.org/pdf/1806.05293 | vote 3-0

- **Multi-asset Kelly fractions can be computed by solving a linear matrix equation f = M^{-1} b, where the matrix M and vector b involve only the first and second moments (means, variances, covariances) of the joint return distribution — i.e., multi-asset Kelly with covariance reduces to a matrix inversion.**
  Source: https://arxiv.org/pdf/1806.05293 | vote 3-0

- **Positive correlation between assets reduces the optimal Kelly fractions and negative correlation increases them, consistent with diversification logic; in the limiting case of two identical perfectly correlated stocks (rho = 1), each optimal fraction is exactly half the single-stock Kelly fraction.**
  Source: https://arxiv.org/pdf/1806.05293 | vote 3-0

- **The continuous-time Kelly criterion gives an optimal fraction f* = (mu - r)/sigma^2 for a single risky asset, and for n risky assets the optimal vector generalizes to F* = Sigma^{-1}(mu - r*1), i.e., the inverse covariance matrix times the excess-return vector.**
  Source: https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full | vote 3-0

- **Betting a multiple of the Kelly fraction is catastrophic: in the paper's empirical single-stock test (Banca Intesa, 2007–2018), triple Kelly produced a 94.3% maximum drawdown and negative CAGR (−0.59%), while half Kelly cut max drawdown to 25% versus 48.4% for full Kelly, at the cost of only ~0.55 percentage points of CAGR (2.72% vs 3.27%).**
  Source: https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full | vote 3-0

- **Estimation error in the inputs (mu, Sigma) effectively causes over-betting relative to the true optimum, which the authors identify as a practical danger motivating fractional Kelly; an investor wanting lower risk should scale down to a fractional Kelly strategy.**
  Source: https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full | vote 3-0

- **Simple normal-GARCH VaR models that passed backtests pre-crisis failed during 2008, while an asymmetric GARCH with skewed Student-t innovations (AR(1)-APARCH(1,1)-skT) still produced adequate one-day-ahead 95% VaR forecasts during the 2008 crisis year.**
  Source: https://www.researchgate.net/publication/227430024_Evaluating_value-at-risk_models_before_and_after_the_financial_crisis_of_2008_International_evidence | vote 3-0

- **During 2008, simple VaR models materially underestimated tail risk on major indices: for the S&P 500 the EWMA (RiskMetrics) 95% one-day VaR was violated on 8.7% of days (vs 5% expected; Kupiec p=0.01, rejected) and for the FTSE 100 on 9.1% of days, while the APARCH-skT model's violation rates (5.9% and 6.3%) remained statistically acceptable.**
  Source: https://www.researchgate.net/publication/227430024_Evaluating_value-at-risk_models_before_and_after_the_financial_crisis_of_2008_International_evidence | vote 3-0

- **The paper's headline conclusion pushes back on the narrative that VaR as a technique failed in 2008: properly specified ARCH-family VaR forecasting worked satisfactorily even during the extreme volatility of 2008, so quantitative risk models alone should not be blamed for the crisis.**
  Source: https://www.researchgate.net/publication/227430024_Evaluating_value-at-risk_models_before_and_after_the_financial_crisis_of_2008_International_evidence | vote 3-0

- **Kyle's model has a unique linear equilibrium with closed forms: the insider's demand is X(v) = beta(v - p0) and the market maker's pricing rule is P = p0 + lambda(x + u), where beta = (sigma_u^2/Sigma_0)^(1/2) and lambda is proportional to (Sigma_0/sigma_u^2)^(1/2) — i.e., price impact rises with the variance of private information and falls with noise-trading variance.**
  Source: https://people.duke.edu/~qc2/BA532/1985%20EMA%20Kyle.pdf | vote 3-0

- **Uninformed (noise) traders systematically lose to the informed trader because market makers cannot distinguish informed from uninformed order flow — adverse selection is structural, and the informed trader's profits come directly at the expense of uninformed flow. This is the formal basis for treating 'your counterparty knowing more than you' as the base case for anonymous market orders.**
  Source: https://people.duke.edu/~qc2/BA532/1985%20EMA%20Kyle.pdf | vote 3-0

- **A trader with an informational edge optimally trades on it gradually rather than all at once, so that in the continuous-auction limit prices follow Brownian motion, market depth is constant, and all private information is incorporated into prices only by the end of trading — the canonical model of strategic edge exploitation under price impact.**
  Source: https://people.duke.edu/~qc2/BA532/1985%20EMA%20Kyle.pdf | vote 3-0

