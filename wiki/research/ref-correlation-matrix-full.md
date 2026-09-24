---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
generated: 2026-08-24 by correlation-matrix subagent (factors.db bars, 90d window)
tags:
  - topic/investing
  - topic/portfolio-construction
  - topic/correlation
  - thesis/theme-alpha
related: ["[[ref-correlation-matrix-full]]", "ref-supply-chain-dependency", "ref-factor-lens", "investing-moc"]
---

# Full Pairwise Correlation Matrix (90-day)

GENERATED: 2026-08-24 from Efforts/osanwe-v2-overhaul/_work/factors.db (bars table:
ticker/date/close). 106 instruments x 90 daily returns (window 2026-04-14 through
2026-08-21; equity trading-day grid). Pearson correlations on simple daily returns.
5,565 pairs computed. Excluded: SPCX (49 bars, insufficient window history).

## Headline numbers

| Metric | Value |
|---|---|
| Instruments in DB | 107 |
| Instruments with enough window history | 106 (SPCX dropped) |
| Pairs computed | 5,565 |
| Mean pairwise rho | 0.235 |
| Median pairwise rho | 0.232 |
| Pairs with rho > 0.80 | 69 |
| Pairs with rho > 0.90 | 11 |
| Pairs with rho > 0.75 | 127 |
| Effective independent bets (all 106, participation ratio) | ~7.4 |
| Effective bets vs nominal count | 7% of headline diversification |

Interpretation: the watchlist behaves like roughly SEVEN independent bets despite
107 tickers. One market/semis factor dominates.

## 1. Top-20 most-correlated pairs

All 20 exceed rho 0.80 (task bar). Class: BETA = sector beta pair, same theme, different instruments.

| # | A | B | rho | Class | Reading |
|---|---|---|-----|-------|---------|
| 1 | SPY | VOO | 0.999 | BETA | Same index twice; VOO -> SPY is a redundant proxy |
| 2 | ITA | PPA | 0.964 | BETA | Defense/aerospace ETF twins |
| 3 | QQQ | VGT | 0.958 | BETA | Tech-index twins |
| 4 | PPA | XAR | 0.951 | BETA | Defense ETF cluster core |
| 5 | QQQ | SMH | 0.922 | BETA | Semis now ARE the Nasdaq |
| 6 | AMAT | LRCX | 0.918 | BETA | Semicap equipment duopoly co-movement |
| 7 | SMH | VGT | 0.918 | BETA | VGT is ~1/4 semis already |
| 8 | QQQ | SPY | 0.918 | BETA | Broad-index convergence |
| 9 | QQQ | VOO | 0.917 | BETA | Broad-index convergence |
| 10 | ITA | XAR | 0.915 | BETA | Defense ETF cluster |
| 11 | DUK | SO | 0.902 | BETA | Regulated utilities rate-trade pair |
| 12 | LRCX | SMH | 0.899 | BETA | Equipment = semis beta amplifier |
| 13 | AMAT | KLAC | 0.885 | BETA | Semicap process-control + deposition |
| 14 | DTCR | SMH | 0.882 | BETA | DTCR trades as a semis derivative |
| 15 | KLAC | SMH | 0.880 | BETA | Equipment = semis beta |
| 16 | ETN | VOLT | 0.875 | BETA | VOLT's largest driver is grid-equipment mega-caps |
| 17 | KLAC | LRCX | 0.872 | BETA | Semicap trio closes ranks |
| 18 | LRCX | MKSI | 0.872 | BETA | Equipment + laser optics supply chain |
| 19 | AMAT | SMH | 0.870 | BETA | Equipment = semis beta |
| 20 | BTC-USD | XRP-USD | 0.866 | BETA | Crypto complex moves as one risk asset |

Near misses (0.85-0.86): MKSI-ONTO 0.864, OKLO-SMR 0.864, MP-USAR 0.861,
AMAT-MKSI 0.859, ASML-LRCX 0.859, VGT-VOO 0.858, AMD-SMH 0.856,
SPY-VGT 0.856, COHR-LITE 0.852.

## 2. Cluster identification -- which names are ONE bet

Union-find components on the full 106-name graph at rho > 0.75:

| Cluster | Members | Internal avg rho | What it is |
|---|---|---|---|
| Mega-cluster | 30 names: AAOI, ABBNY, AEIS, ALAB, AMAT, AMD, AMKR, ASMIY, ASML, COHR, DTCR, ETN, FN, INTC, KLAC, LITE, LRCX, MKSI, MRVL, MU, ONTO, QQQ, SMH, SNDK, SPY, TSM, VGT, VOLT, VOO, VRT | n/a | ONE bet: AI-infrastructure/market factor. Contains the semis and ETF cluster |
| Defense | ITA, NOC, PPA, RTX, XAR (+LMT/GD/HII/LHX/KTOS/AVAV loosely) | 0.59 | ONE bet: defense budgets |
| Regulated utilities | AEP, DUK, NEE, PPL, SO | 0.68 | ONE bet: rates (negatively correlated to SPY here: DUK -0.28, SO -0.23) |
| Crypto | BTC-, SOL-, XRP-, LINK-USD (+COIN, ONDO, HBAR, QNT, ALGO loosely) | 0.76 | ONE bet: crypto risk factor |
| IPP power | CEG, VST, TLN, NRG | 0.76 avg, 0.63-0.82 range | ONE bet: merchant power / hyperscaler PPAs |
| Nuclear new-build | OKLO + SMR (0.86 pair), BWXT adjacent | 0.64 | ONE bet: SMR speculation |

Thematic group internal correlations (avg pairwise within theme):

```
semi-equipment   (15 pairs)  avg 0.83   <-- tightest true sector block
memory           (MU,SNDK,WDC) avg 0.76  max MU-SNDK 0.84
crypto           (10 pairs)  avg 0.76
ipp-power        (CEG,VST,TLN,NRG) avg 0.76
optical          (COHR,LITE,AAOI,MKSI) avg 0.71
regulated-util   (5 names)   avg 0.68
nuclear          (OKLO,BWXT,SMR) avg 0.64
defense          (6 names)   avg 0.59
hyperscaler      (MSFT,GOOGL,META,AMZN) avg 0.33  <-- NOT one trade at 90d
```

Key structural findings:

- WDC sits OUTSIDE the rho>0.75 mega-cluster (top edges: MKSI/LRCX/SNDK all
  0.73) -- HDD post-spin has decoupled from NAND/memory proper. MU+SNDK+WDC are
  NOT an undifferentiated "memory" block anymore: MU-SNDK 0.84, but WDC adds a
  genuinely different storage-cycle return stream.
- The CEG+VST+TLN power IPP block is real but looser than assumed (avg 0.76;
  CEG-NRG only 0.69). It is ONE regulatory/AI-power-demand bet at portfolio level.
- Hyperscalers (MSFT/GOOGL/META/AMZN avg 0.33) are four DIFFERENT bets at 90d --
  idiosyncratic earnings dominate; do not treat them as one "megacap tech" line.
- Tight cores at rho > 0.85: {AMAT, AMD, ASML, DTCR, KLAC, LRCX, MKSI, ONTO,
  QQQ, SMH, SPY, VGT, VOO} form a single 13-name clique-like core -- owning any
  three of these is approximately owning one position.

## 3. Diversification score

Method 1 -- participation ratio of the 106x106 eigen-spectrum:
N_eff = (sum lambda)^2 / sum(lambda^2) ~= 7.36 effective bets out of 106 names.

Method 2 -- average-correlation closed form (m / (1+(m-1)*rho_avg)):
N_eff ~= 4.13 (pessimistic bound; assumes equicorrelation).

PC1 explains 34% of total variance; top 5 eigenmodes explain 57%; top 10
explain 69%. The remaining ~31% is idiosyncratic spread across ~96 residual
directions -- real single-name alpha exists but is a minority of variance.

Verdict: 106 nominal instruments ~= 7 truly independent bets:

```
1. AI-semis/market mega-factor (~everything in the 30-name mega-cluster)
2. Defense budgets
3. Rates / regulated utilities (negative-beta ballast)
4. Crypto complex
5. Merchant power IPPs
6. Nuclear new-build (overlaps #5 economically)
7. Residual idiosyncratic sleeve (hyperscalers, PLTR-type names, WBD, HIMS...)
```

## 4. Portfolio-specific warnings

Withheld from the public copy: this section named individual positions, their pairwise correlations and the resulting concentration verdicts.


## Caveats

- 90 trading days ending 2026-08-21; regime-specific (post-April window includes
  the semis correction legs). Correlations are unstable across regimes; re-run
  after any >5% SPY drawdown week.
- Daily-return Pearson understates tail co-movement; stress correlations run
  higher than this matrix shows.
- SPCX excluded (IPO-window history shorter than minimum overlap).
- HOOD absent from bars -- ingest gap, not a zero-correlation finding.

GENERATED: 2026-08-24 by correlation-matrix subagent from factors.db (no network).
Reproduce: python against bars table, 90-return window, Pearson on shared dates.
