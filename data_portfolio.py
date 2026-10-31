import pandas as pd


def portfolio_data():
    return pd.DataFrame([
        ['Meridian Cloud','Software',80,0.060,0.28,3.2,4.8,1.55,99,180,6.5],
        ['Atlas Health','Healthcare',105,0.035,0.22,2.4,4.1,1.90,100,95,5.2],
        ['Forge Industrial','Industrials',95,0.045,0.30,3.8,4.9,1.70,98,125,4.7],
        ['Harbor Consumer','Consumer',70,0.085,0.38,2.0,5.6,1.30,95,210,7.1],
        ['Nexus Services','Business Services',120,0.040,0.24,3.0,4.5,1.80,99,110,5.5],
        ['Pioneer Logistics','Logistics',90,0.055,0.32,2.7,5.1,1.45,97,165,6.2],
        ['Solstice Energy','Energy',110,0.050,0.27,4.1,4.7,1.65,98,150,5.9],
        ['Beacon Receivables','Asset-backed',130,0.025,0.18,1.3,3.2,2.30,100,45,3.8],
    ], columns=['asset','sector','exposure','pd','lgd','duration','leverage','coverage','mark','days_to_liquidate','spread'])
