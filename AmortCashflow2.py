# amortization cashflow
# prepay, default, severity, delinquency assumption included

import pandas as pd
import numpy as np
import numpy_financial as npf

# assumption set
wac = 0.2; term = 60 ; upb = 1 * 1e8; serviceFee = 0.001
cdrVector = np.array([0] + [0.10] * term)
cprVector = np.array([0] + [0.07] * term)
sevVector = np.array([0] + [0.60] * term)
dqVector = np.array([0] + [0.02] * term)

smmVector = 1 - (1 - cprVector) ** (1 / 12)
mdrVector = 1 - (1 - cdrVector) ** (1 / 12)

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
            list(
                zip(
                    periods,
                    periodsYears,
                    amortSchedPeriodic,
                    cdrVector,
                    mdrVector,
                    cprVector,
                    smmVector,
                    sevVector,
                    dqVector,
                )
            ),
            columns=[
                "period",
                "periodYears",
                "amortSchedPeriodic",
                "cdrVector",
                "mdrVector",
                "cprVector",
                "smmVector",
                "sevVector",
                "dqVector",
            ],
        )


cashflow["amortBalPeriodic"] = upb - cashflow["amortSchedPeriodic"].cumsum()
        
cashflow["balFactor"] = (
    cashflow["amortBalPeriodic"]
    .div(cashflow["amortBalPeriodic"].shift())
    .fillna(1)
)
cashflow[
    [
        "bopBal",
        "perfBal",
        "dqBal",
        "prepayPrin",
        "intCF",
        "servicingFees",
        "netIntCF",
        "defaultPrin",
        "lossPrin",
        "recoveryPrin",
        "schedPrin",
        "prinCF",
        "eopBal",
    ]
] = np.nan

cashflow[["servicingFeesRatio"]] = serviceFee
for i, row in cashflow.iterrows():

    if row["period"] == 0:
        cashflow.loc[
            i,
            [
                "bopBal",
                "perfBal",
                "dqBal",
                "prepayPrin",
                "intCF",
                "servicingFees",
                "netIntCF",
                "defaultPrin",
                "lossPrin",
                "recoveryPrin",
                "schedPrin",
                "prinCF",
            ],
        ] = 0
        cashflow.at[i, "eopBal"] = upb
    else:
        cashflow.at[i, "bopBal"] = cashflow.loc[i - 1, "eopBal"]
        cashflow.at[i, "defaultPrin"] = cashflow.at[i, "bopBal"] * cashflow.at[i, "mdrVector"]
        cashflow.at[i, "lossPrin"] = cashflow.at[i, "defaultPrin"] * cashflow.at[i, "sevVector"]
        cashflow.at[i, "recoveryPrin"] = cashflow.at[i, "defaultPrin"] - cashflow.at[i, "lossPrin"]
        nonDefaultPrin = cashflow.at[i, "bopBal"] - cashflow.at[i, "defaultPrin"]
        cashflow.at[i, "perfBal"] = nonDefaultPrin * (1 - cashflow.at[i, "dqVector"])
        cashflow.at[i, "dqBal"] = nonDefaultPrin - cashflow.at[i, "perfBal"]
        cashflow.at[i, "intCF"] = cashflow.at[i, "perfBal"] * wac / 12
        cashflow.at[i, "prepayPrin"] = cashflow.at[i, "perfBal"] * cashflow.at[i, "smmVector"]
        cashflow.at[i, "schedPrin"] = (nonDefaultPrin - cashflow.at[i, "prepayPrin"]) * (1 - cashflow.at[i, "balFactor"])
        cashflow.at[i, "prinCF"] = (
                    cashflow.at[i, "schedPrin"]
                    + cashflow.at[i, "recoveryPrin"]
                    + cashflow.at[i, "prepayPrin"]
                )
        cashflow.at[i, "eopBal"] = (
                    cashflow.at[i, "bopBal"]
                    - cashflow.at[i, "schedPrin"]
                    - cashflow.at[i, "defaultPrin"]
                    - cashflow.at[i, "prepayPrin"]
                )

        servicingFeesDue = (
            np.average([cashflow.at[i, "bopBal"], cashflow.at[i, "eopBal"]])
            * cashflow.at[i, "servicingFeesRatio"]
            / 12.0
        )
        cashflow.at[i, "servicingFees"] = min(cashflow.at[i, "intCF"], servicingFeesDue)
        cashflow.at[i, "netIntCF"] = (
                    cashflow.at[i, "intCF"] - cashflow.at[i, "servicingFees"]
                )