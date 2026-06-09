## Capstone: Enterprise Risk Management

Enterprise Risk Management (ERM) integrates all major forms of financial risk—market, credit, liquidity, and operational—into a unified framework for evaluating firm-wide stability.

Unlike individual case studies that isolate specific failure mechanisms, the ERM capstone examines how risks interact, amplify each other, and ultimately determine a bank’s overall resilience under stress.

This analysis reflects real-world practices used by global banks, regulators, and Chief Risk Officers to:

- Evaluate enterprise-wide exposure  
- Conduct integrated stress testing  
- Assess capital and liquidity adequacy  
- Support board-level decision making  

→ View ERM Analysis → [View Executive Summary](cases/erm_summary.md/)

## Featured Insights

### LTCM — Model Risk and Correlation Breakdown

!!! note ""

    **Insight:** Statistical models fail when assumptions break under stress.

    **Quant Takeaway:** Volatility and correlation estimates derived from stable regimes understate joint tail risk, causing portfolio risk to increase nonlinearly under stress.

    **Model Implication:** Risk models must be supplemented with stress scenarios and correlation breakdown assumptions, particularly before applying leverage to convergence strategies.
    
    - Regime shifts invalidate calibration
    - Correlations converge under stress
    - Leverage amplifies model error


    **Further Analysis:** [View Executive Summary](cases/ltcm_summary.md)


---

### Lehman Brothers — Liquidity and Confidence Collapse

!!! note ""

    **Insight:** Institutions fail when funding disappears—not when capital first appears insufficient.

    **Quant Takeaway:** Balance sheet solvency metrics remained relatively stable, while effective liquidity risk increased discontinuously due to funding withdrawal and valuation uncertainty.

    **Model Implication:** Risk management frameworks must treat liquidity as a binding constraint and incorporate funding stress scenarios alongside capital adequacy measures.
    
    - Capital vs balance-sheet vulnerability  
    - Liquidity vs solvency breakdown  
    - Confidence erosion drives collapse  

    **Further Analysis:** [View Executive Summary](cases/lehman_summary.md)

---

### London Whale — VaR Failure and Tail Risk

!!! note ""

    **Insight:** Measuring probability of loss is not the same as understanding magnitude.

    **Quant Takeaway:** VaR remains insensitive to tail severity, while Expected Shortfall reveals substantially larger losses under stress scenarios, indicating hidden downside exposure.

    **Model Implication:** Institutions should rely on tail-sensitive metrics such as Expected Shortfall and explicitly manage concentration risk rather than relying solely on VaR thresholds.
    
    - VaR vs Expected Shortfall (ES)  
    - Tail risk revealed under stress  
    - Model limitations exposed  

    **Further Analysis:** [View Executive Summary](cases/london_whale_summary.md)
    
---

### Global Financial Crisis — Systemic Risk Interaction

!!! note ""

    **Insight:** Systemic crises occur when multiple risk models fail simultaneously.

    **Quant Takeaway:** CDS-implied risk (~4% for BBB), structural credit signals (Z ≈ distress), and portfolio models (WCDR ≈ 3%, CVA ≈ $52.8k) diverge significantly under stress, signaling model breakdown.

    **Model Implication:** Risk management must integrate credit, market, liquidity, and counterparty models rather than relying on any single framework.

    - CDS vs historical PD divergence  
    - Altman Z reveals hidden fragility  
    - VaR underestimates systemic loss  
    - CVA exposes counterparty risk  
    - Wrong-way risk amplifies losses  

    **Further Analysis:** [View Executive Summary](cases/gfc_summary.md)

---

### Sunrise National Bank — Stress Testing and Scenario Analysis

!!! note ""

    **Insight:** Stress testing reveals vulnerabilities that are not observable under baseline or historical conditions.

    **Quant Takeaway:** Under stress scenarios, SNB’s CET1 ratio declines sharply (≈4.8%, ≈3.1%, ≈4.3%), with the supervisory scenario breaching regulatory minimums and losses driven primarily by credit exposure.

    **Model Implication:** Risk management must rely on forward-looking scenario analysis and integrate credit, market, and liquidity interactions rather than relying on static capital ratios.

    - Capital adequacy diverges significantly under stress conditions  
    - Credit losses dominate total losses across scenarios  
    - Market and liquidity shocks amplify capital deterioration  
    - Reverse stress testing identifies non-linear failure thresholds  
    - Scenario design captures interaction effects across risk categories  

    **Further Analysis:** [View Executive Summary](cases/snb_summary/)

---

### Atlas Bank International — Basel Regulation and Risk Transformation

!!! note ""

    **Insight:** Regulatory frameworks shape how risk is measured and can create incentives that amplify systemic vulnerabilities.

    **Quant Takeaway:** ABI’s pre-crisis VaR (~$35–42M) failed to capture realized losses that escalated to ~$4.5B during the financial crisis, while Basel II.5 increased trading-book capital requirements to over $3B under stressed conditions. 

    **Model Implication:** Risk management must supplement internal models with stressed risk measures, capital buffers, and liquidity constraints to prevent underestimation of tail risk and excessive leverage.

    - Basel I enabled regulatory arbitrage through coarse risk weights 
    - Basel II internal models underestimated risk during low-volatility periods 
    - VaR failed to capture extreme tail losses during the crisis 
    - Basel II.5 introduced sVaR, IRC, and CRM to correct trading-book weaknesses 
    - Basel III strengthened CET1, leverage constraints, and liquidity standards 

    **Further Analysis:** [View Executive Summary](cases/abi_summary/)

---

## Analytical Framework

Across all cases, the lab applies a consistent approach:

- **Measure risk** using quantitative models  
- **Evaluate model behavior** under stress conditions  
- **Identify failure mechanisms**  
- **Translate insights into risk management actions**  

---

## Guiding Principle

> Financial failures are not caused by a single error,  
> but by the interaction of **models, markets, and human decisions**.
