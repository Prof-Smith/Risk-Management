# Northstar VaR & CVaR Shock Lab

This version deliberately centers one event and one analytical engine.

## Event
AI-driven repricing of software credit, beginning with Meridian Cloud and spilling into the broader private-debt portfolio.

## Core calculations
- Monte Carlo portfolio loss distribution
- VaR at the selected confidence level
- CVaR at the selected confidence level

## Derived calculations
- Change in VaR
- Change in CVaR
- CVaR minus VaR tail gap
- Borrower contribution in scenarios beyond VaR
- Numerical CVaR reversal condition

## Story
Portfolio → Shock mechanics → Tail anatomy → Committee decision

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```
