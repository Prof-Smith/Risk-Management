# JPMorgan London Whale (2012) — Tail Risk and Model Failure

---

## Executive Summary

The JPMorgan London Whale incident illustrates how sophisticated risk models can obscure, rather than reveal, true risk exposure when applied without proper scrutiny.

Despite relying on established Value-at-Risk (VaR) frameworks, the bank incurred losses exceeding $6 billion due to large, concentrated positions in credit derivatives that were not adequately captured by standard risk metrics.

---

## Core Problem

At the center of the failure was a combination of:

- **Overreliance on Value-at-Risk (VaR) as a primary risk metric**  
- **Underestimation of tail risk in portfolio return distributions**  
- **Significant concentration in illiquid credit positions**  
- **Inadequate internal controls and oversight of risk limits**  

Although reported risk measures appeared manageable, they failed to capture the magnitude of potential extreme losses.

---

## Analytical Approach

Using a simulated credit derivatives portfolio, the analysis evaluates:

- Value-at-Risk (VaR) across parametric, historical, and Monte Carlo methods  
- Expected Shortfall (ES) as a complementary tail risk measure  
- Differences in risk estimates under pre-stress and stress conditions  
- Distributional characteristics of returns, including extreme tail behavior  

---

## Key Findings

- VaR estimates remained relatively stable even under stress conditions  
- Expected Shortfall (ES) increased significantly, revealing large tail losses  
- The distribution of returns exhibited negative skew and fat tails  
- Stress scenarios exposed losses far exceeding VaR thresholds  

These results demonstrate that standard VaR measures can severely understate risk in the presence of extreme events.

---

## Key Insight

> VaR measures the probability of loss up to a threshold,  
> but does not capture the magnitude of losses beyond that point.

This limitation makes VaR particularly unreliable in environments characterized by tail risk and market stress.

---

## Implications for Risk Management

- Firms must supplement VaR with tail-sensitive measures such as Expected Shortfall  
- Concentration risk must be monitored alongside statistical risk metrics  
- Stress testing should play a central role in risk assessment  
- Risk governance must ensure that model outputs are critically evaluated—not accepted mechanically  

---

## Position Within Risk Framework

-	LTCM → Model failure
-	Lehman → Liquidity failure
-	London Whale → Measurement failure
 
---

## Full Analysis

- 📄 [Assignment](cases/london_whale_assignment.md)  
- 📓 [Lab Notebook](cases/london_whale_notebook.ipynb)  
