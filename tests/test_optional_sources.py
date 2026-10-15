import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import analyse
import clean


def test_optional_register_loads_every_row_and_filters_by_explicit_iso_end_date(tmp_path,monkeypatch):
    (tmp_path/'data').mkdir()
    pd.DataFrame([{'supplier':f'Fixture {i} Ltd','start_date':'2025-01-01',
                   'end_date':'2025-12-31' if i==0 else '2027-01-01','value':10000} for i in range(7)]).to_csv(tmp_path/'data/contract-register.csv',index=False)
    monkeypatch.setattr(clean,'ROOT',tmp_path);monkeypatch.setattr(clean,'OUT',tmp_path)
    register,log=clean.load_register(date(2026,5,1))
    assert len(register)==7 and register['active'].sum()==6
    assert set(register.source)=={'register'} and log['register_present']


def test_register_only_exact_match_is_used_when_contract_notice_export_absent(tmp_path,monkeypatch):
    monkeypatch.setattr(analyse,'FULL',tmp_path)
    agg=pd.DataFrame([{'supplier_norm':'FIXTURE','supplier_name':'Fixture','annualised_estimate':40000,
                       'total_gbp':10000,'n_payments':1,'narrative':'IT','service':'Finance','dominant_tag':'general_procurement'}])
    register=pd.DataFrame([{'supplier_norm':'FIXTURE','active':True,'source':'register'}])
    result,_=analyse.off_contract(agg,register,False,True,{'value':25000,'inclusive':True,'rule_ids':['PUB']})
    assert result['counts_by_match_class'][0]['match_class']=='exact'
    assert pd.read_csv(tmp_path/'supplier-match.csv').iloc[0].candidate_source=='register'


def test_supplied_statutory_parameter_runs_its_supplier_tier(tmp_path,monkeypatch):
    monkeypatch.setattr(analyse,'FULL',tmp_path)
    spend=pd.DataFrame([{'supplier_norm':'FIXTURE','Supplier name':'Fixture Ltd','Net amount':10000,
                         'Narrative':'IT','Service':'Finance','tag':'general_procurement','row_id':'f.xlsx:2'}])
    result,skipped,_,_=analyse.high_value_suppliers(spend,3,
        [{'value':1000,'competition_triggering':True,'rule_ids':['X']}],
        {'STATUTORY_THRESHOLD_GOODS_SERVICES':{'value':30000}})
    tier=result['statutory_tiers']['STATUTORY_THRESHOLD_GOODS_SERVICES']
    assert tier['count']==1 and tier['threshold']==30000
    assert not skipped
