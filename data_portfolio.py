import pandas as pd

def portfolio_data():
    return pd.DataFrame([
        ['Ghostline Systems','Software',80,0.060,0.28,99],
        ['Axiom Surgical','Healthcare',105,0.035,0.22,100],
        ['Ironveil Manufacturing','Industrials',95,0.045,0.30,98],
        ['Vicehouse Brands','Consumer',70,0.085,0.38,95],
        ['CipherWorks','Business services',120,0.040,0.24,99],
        ['Dead Reckoning Logistics','Logistics',90,0.055,0.32,97],
        ['Blackflare Energy','Energy',110,0.050,0.27,98],
        ['Cold Harbor Receivables','Asset-backed',130,0.025,0.18,100],
    ],columns=['asset','sector','exposure','pd','lgd','mark'])
