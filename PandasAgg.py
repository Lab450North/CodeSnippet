import pandas as pd
import numpy as np
loanTape = pd.read_csv('loantape.20200131.csv')

# convert to datetime and date
loanTape['Snapshotdt_datetime'] = pd.to_datetime(loanTape['Snapshotdt'])
loanTape['Snapshotdt_dt'] = loanTape['Snapshotdt_datetime'].dt.date

# aggregation
# loanTape['LoanStatus2'].value_counts()

res = loanTape.groupby(['LoanStatus2'])[['CurrentRate','OriginalPayment']].agg(
    count = ('OriginalPayment',np.size),
    sumAmount = ('OriginalPayment',np.sum),
    maxRate = ('CurrentRate',np.max),
    minRate = ('CurrentRate',np.min),
    wtAvgRate = ('CurrentRate',lambda x: 0 if loanTape.loc[x.index, 'OriginalPayment'].sum() == 0 else np.average(x, weights = loanTape.loc[x.index, 'OriginalPayment'])),
    avgRate = ('CurrentRate',np.mean)
    )

# multiple level index
loanTape = loanTape.set_index(['LoanStatus2','ApplicationID'])

idx = pd.IndexSlice
# only show Current
# print(loanTape.loc[idx['EarlyDQ',:],:])
# only show 10000318
# print(loanTape.loc[idx[:,10000318],:])


# create new column based off other two column
def newColMap(x):
    return x['CurrentRate'] * x['OriginalPayment']

loanTape.loc[:,'NewCol'] = loanTape.loc[:, ['CurrentRate','OriginalPayment']].apply(lambda x: newColMap(x), axis = 1)

