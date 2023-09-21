# plain vanilla amortization cashflow
# no prepay, default, delinquency assumption


import pandas as pd
import numpy as np
import numpy_financial as npf

# assumption set
wac = 0.2; term = 60 ; upb = 1 * 1e8; serviceFee = 0.001


amortSchedPeriodic = np.concatenate(
            [
                np.array([0]),
                npf.ppmt(
                    wac / 12,
                    np.arange(term) + 1,
                    term,
                    -upb,
                ),
            ]
        )
periods = np.array(range(0, term + 1))
periodsYears = np.floor_divide(periods-1, 12) + 1
cashflow = pd.DataFrame(
    list(zip(periods, periodsYears,amortSchedPeriodic)),
    columns=["period","periodYears","amortSchedPeriodic"],
)
cashflow["amortBalPeriodic"] = upb - cashflow["amortSchedPeriodic"].cumsum()
        
cashflow["balFactor"] = (
    cashflow["amortBalPeriodic"]
    .div(cashflow["amortBalPeriodic"].shift())
    .fillna(1)
)

cashflow[["bopBal","intCF", "servicingFees", "netIntCF", "schedPrin","prinCF","eopBal"]] = np.nan
cashflow[["servicingFeesRatio"]] = serviceFee

for i, row in cashflow.iterrows():
    if row["period"] == 0:
        cashflow.loc[i,["bopBal","intCF","servicingFees","netIntCF","schedPrin","prinCF"]] = 0
        cashflow.at[i, "eopBal"] = upb
    else:
        cashflow.at[i, "bopBal"] = cashflow.loc[i - 1, "eopBal"]
        cashflow.at[i, "intCF"] = cashflow.loc[i, "bopBal"] * wac / 12
        cashflow.at[i, "servicingFees"] = cashflow.loc[i, "bopBal"] * serviceFee / 12
        cashflow.at[i, "netIntCF"] = cashflow.at[i, "intCF"] - cashflow.at[i, "servicingFees"]
        cashflow.at[i, "schedPrin"] =  cashflow.at[i, "bopBal"] * (1 - cashflow.at[i, "balFactor"])
        cashflow.at[i, "prinCF"] = cashflow.at[i, "schedPrin"]
        cashflow.at[i, "eopBal"] = cashflow.at[i, "bopBal"] - cashflow.at[i, "schedPrin"]

