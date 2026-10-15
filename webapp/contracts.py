"""Constrained API response shapes; audit meaning is checked by the original tools.

Sample recipes travel as JSON text to keep the compiled API grammar small.
They are parsed losslessly before the original sample validator sees them.
"""
import copy

TEXT={'type':'string'}
INTEGER={'type':'integer'}
BOOLEAN={'type':'boolean'}

def array(item):return {'type':'array','items':item}
def obj(**fields):
    return {'type':'object','properties':fields,'required':list(fields),'additionalProperties':False}
def enum(*values):return {'type':'string','enum':list(values)}
def ref(name):return {'$ref':'#/$defs/'+name}

STRINGS=array(TEXT)
CONTROL=obj(id=TEXT,control=TEXT,cites=STRINGS,owner=TEXT)
RECIPE={'type':'string','description':'A JSON object encoded as text, using the original sample recipe schema. Filters are ordinary column/value dictionaries. Include only fields needed for this sample.'}
TEST=obj(id=TEXT,control=TEXT,step=TEXT,evidence=TEXT,cites=STRINGS,sample_json=RECIPE,pbc=STRINGS)
PLAN=obj(generated_at=TEXT,memo=obj(purpose=STRINGS,background=STRINGS,approach=STRINGS,limitations=STRINGS),
    risks=array(obj(id=TEXT,objective=TEXT,controls=array(ref('control')),tests=array(ref('test')))),
    rules_not_tested=array(obj(reason=TEXT,rule_ids=STRINGS)))
PLAN['properties']['preparation_status']=TEXT
PLAN_DEFS={'control':CONTROL,'test':TEST}
RESPONSE=obj(id=INTEGER,decision=enum('accepted','declined','for the auditor'),explanation=TEXT)
GRADE=obj(score=INTEGER,justification=TEXT)
RISK=obj(id=TEXT,title=TEXT,risk=TEXT,
    likelihood=obj(base_score=INTEGER,score=INTEGER,justification=TEXT),impact=GRADE,
    evidence=STRINGS,proposed_focus=TEXT,recommend_in_scope=BOOLEAN,sample_source=TEXT)
RISK['properties']['likelihood']['properties']['repeat_audit_id']=TEXT
STATUS=obj(id=INTEGER,status=enum('resolved','declined','for the auditor'),resolution=TEXT)
FINDING=obj(type=enum('sample','control','test','coverage','rating','scope'),risk=TEXT,
    challenge=TEXT,evidence=TEXT,ask=TEXT)

def response_contract(role,instructions):
    """Return wire schema and whether the planner is answering challenges."""
    task=instructions.rsplit('CURRENT TASK:\n',1)[-1]
    reply=role=='planner' and '"responses"' in task
    if role=='planner':
        schema=obj(plan=PLAN,responses=array(RESPONSE));schema['$defs']=PLAN_DEFS
    elif role=='risk-assessor':
        schema=obj(generated_at=TEXT,risks=array(RISK),excluded=array(obj(theme=TEXT,reason=TEXT)))
    elif role=='challenger':
        schema=obj(summary=TEXT,challenges=array(FINDING),statuses=array(STATUS),additional_blockers=STRINGS)
    elif role=='qa-reviewer':
        schema=obj(verdict=enum('ready','blocked'),summary=TEXT,issues=STRINGS)
    else:raise ValueError('Unknown audit role')
    return copy.deepcopy(schema),reply

TRANSPORT_NOTE=('Follow the API response schema. Planner responses always contain plan and responses '
    '(responses is empty unless the task requests challenge responses). In each test, sample_json '
    'is a JSON-encoded string containing the original sample recipe object, with ordinary filter '
    'dictionaries and the original numeric/boolean/list values. The server parses it into sample '
    'before validation. Do not introduce alternate filter formats. Use an empty owner string when '
    'no owner is named in the source. Challenger arrays that are not requested are empty. These are transport '
    'conventions, not permission to change evidence, scope, ratings or approval.')

def restore_artifact(role,value,reply=False):
    if role!='planner':return value
    value=copy.deepcopy(value);plan=value['plan']
    for risk in plan['risks']:
        for control in risk['controls']:
            if not control['owner']:control.pop('owner')
        for test in risk['tests']:
            test['sample']=parse_recipe(test.pop('sample_json'))
    return value if reply else plan

def parse_recipe(text):
    import json
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate sample recipe key')
            result[key]=value
        return result
    value=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Non-finite recipe value')))
    if not isinstance(value,dict):raise ValueError('Sample recipe must be an object')
    return value
