# Knight Capital — Trading Glitch and Operational Failure

---

## Executive Summary

The Knight Capital incident demonstrates how failures in operational controls, model governance, and software deployment can rapidly escalate into catastrophic financial losses.

Within minutes of deployment, faulty code generated millions of erroneous trades, leading to approximately $7 billion in unintended positions and ~$440 million in losses. 

---

## Core Problem

- Lack of change control and testing procedures  
- Failure to deactivate legacy code  
- Absence of real-time safeguards  
- Weak model governance under SR 11 7  

---

## Analytical Approach

- Historical reconstruction of the event  
- Loss estimation using price impact  
- Tail-risk simulation via lognormal distribution  
- Operational risk capital (SMA framework)  
- Simulation of algorithmic trading dynamics  

---

## Key Findings

- Estimated losses (~$420M) closely match realized outcome 
- Losses driven by forced buying and selling under adverse price impact  
- Tail-risk simulation reveals heavy right-tail exposure  
- SMA capital requirement approximates ~$593M  

---

## Key Insight

> Operational failures in automated trading systems can generate losses faster than firms can respond, making governance and controls critical.

---

## Implications for Risk Management

- Strong model governance is essential under SR 11 7  
- Change management processes must be rigorously enforced  
- Real-time monitoring and circuit breakers are critical  
- Operational risk must be treated as a core financial risk  

---

## Position Within Risk Framework

- Knight → Operational and model risk failure  

---

## Full Analysis

- 📄 knight_assignment.md  
- 📓 knight_notebook.ipynb  
