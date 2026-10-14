import pandas as pd,numpy as np
from benchmark.util import ROOT
def test_relations_and_financial_equations_on_public_tables():
    directory=ROOT/'datasets'/'data_analysis';t=pd.read_csv(directory/'transactions.csv');p=pd.read_csv(directory/'products.csv');c=pd.read_csv(directory/'customers.csv');r=pd.read_csv(directory/'regions.csv')
    assert np.allclose(t.revenue,t.quantity*t.selling_price*(1-t.discount),atol=.006)
    assert set(t.product_id)<=set(p.product_id) and set(t.customer_id)<=set(c.customer_id) and set(t.region_id)<=set(r.region_id)
    assert t.transaction_date.str[:7].nunique()==24
