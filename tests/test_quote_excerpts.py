import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('quote_qa',ROOT/'scripts/checks/check_quotes.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)


def test_curly_and_straight_rendered_quotes_are_both_checked():
    rules={'CPR-01':{'verbatim_quote':'A real complete source sentence.'}}
    for text in ['- [rule:CPR-01] clause 4.2, PDF p.3: “A real complete source sentence.”',
                 '- [rule:CPR-01] clause 4.2, PDF p.3: "A real complete source sentence."']:
        count,errors=qa.check_register_excerpts(text,rules)
        assert count==1 and not errors


def test_wrong_curly_quote_and_unparsed_reference_fail():
    rules={'CPR-01':{'verbatim_quote':'A real complete source sentence.'}}
    for text in ['- [rule:CPR-01] clause 4.2: “An invented quotation.”',
                 '- [rule:CPR-01] clause 4.2: missing delimiters']:
        _,errors=qa.check_register_excerpts(text,rules)
        assert errors
