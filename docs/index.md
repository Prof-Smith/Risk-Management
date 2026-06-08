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
