"""Server-side Anthropic Messages transport with explicit completion evidence."""
import hashlib
import json
import os
import re
import time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from jsonschema import Draft202012Validator, ValidationError
from .budget import ApiBudget, BudgetError
from .contracts import response_contract,restore_artifact,TRANSPORT_NOTE

class ProviderError(RuntimeError):
    """Safe error text and optional usage receipt, never provider bodies or keys."""
    def __init__(self,message,receipt=None):
        super().__init__(message);self.receipt=receipt

class AnthropicProvider:
    def __init__(self,api_key,model,transport=None,budget=None):
        self._key=api_key;self.model=model;self.transport=transport;self.budget=budget

    def generate_json(self,role,instructions,context):
        schema,reply=response_contract(role,instructions)
        request={'model':self.model,'system':instructions+'\n'+TRANSPORT_NOTE,
            'messages':[{'role':'user','content':context}],'max_tokens':18000,'stream':True,
            'output_config':{'effort':'low','format':{'type':'json_schema','schema':schema}}}
        parts=[];size=0;message=None;stopped=False;reason=None;usage={};started=time.monotonic()
        try:
            with httpx.Client(transport=self.transport,timeout=httpx.Timeout(180,connect=20)) as client:
                headers={'x-api-key':self._key,'anthropic-version':'2023-06-01','Content-Type':'application/json'}
                reservation=None
                if self.budget:
                    count=client.post('https://api.anthropic.com/v1/messages/count_tokens',headers=headers,
                        json={k:request[k] for k in ('model','system','messages','output_config')})
                    if count.status_code!=200:raise ProviderError('Anthropic token counting failed; no generation request was sent.')
                    try:
                        tokens=count.json()['input_tokens']
                        if not isinstance(tokens,int) or tokens<1:raise ValueError()
                    except (ValueError,KeyError,TypeError):raise ProviderError('Invalid token estimate; no generation request was sent.') from None
                    try:reservation=self.budget.reserve(self.model,tokens,request['max_tokens'])
                    except BudgetError as error:raise ProviderError(str(error)) from None
                with client.stream('POST','https://api.anthropic.com/v1/messages',headers=headers,json=request) as response:
                    if response.status_code!=200:
                        raise ProviderError(f'Anthropic request failed (HTTP {response.status_code}). Check API billing, model access or rate limits; no automatic retry was made.')
                    for line in response.iter_lines():
                        if not line.startswith('data: '):continue
                        try:event=json.loads(line[6:])
                        except ValueError:continue
                        kind=event.get('type')
                        if kind=='message_start':
                            message=event.get('message',{});usage.update(message.get('usage',{}))
                        elif kind=='content_block_start':
                            block=event.get('content_block',{})
                            if block.get('type')=='text':
                                text=block.get('text','');parts.append(text);size+=len(text)
                        elif kind=='content_block_delta' and event.get('delta',{}).get('type')=='text_delta':
                            text=event['delta'].get('text','');parts.append(text);size+=len(text)
                        elif kind=='message_delta':
                            reason=event.get('delta',{}).get('stop_reason',reason);usage.update(event.get('usage',{}))
                        elif kind=='message_stop':stopped=True
                        elif kind=='error':raise ProviderError('Anthropic generation failed. This run is blocked.')
                        if size>600000:raise ProviderError('Model response exceeded the permitted artifact size.')
        except httpx.HTTPError:
            raise ProviderError('The Anthropic connection was interrupted. This run is blocked; no automatic retry was made.') from None
        if not stopped or not message or not message.get('id'):
            raise ProviderError('Anthropic did not finish the response stream. The request remains reserved against the API budget.')
        if self.budget and not all(isinstance(usage.get(k),int) and usage[k]>=0 for k in ('input_tokens','output_tokens')):
            raise ProviderError('Completed generation did not report valid usage; its budget reservation is retained.')
        cost=self.budget.settle(reservation,usage) if self.budget else None
        text=''.join(parts).strip()
        receipt={'role':role,'provider':'anthropic','model':message.get('model',self.model),
            'response_id':message['id'],'completed':reason=='end_turn','stop_reason':reason,
            'at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'elapsed_seconds':round(time.monotonic()-started,2),'usage':usage,
            'output_sha256':hashlib.sha256(text.encode()).hexdigest()}
        if cost is not None:receipt['estimated_cost_usd']=cost
        if reason!='end_turn':
            raise ProviderError('Anthropic stopped with '+str(reason)+'. Incomplete or refused output is blocked; no automatic retry was made.',receipt)
        if text.startswith('```'):text=re.sub(r'^```(?:json)?\s*|\s*```$','',text).strip()
        try:
            value=json.loads(text,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite value')))
            if not isinstance(value,dict):raise ValueError('Object required')
        except ValueError:
            receipt['completed']=False
            raise ProviderError('The completed model response was not a valid JSON object. This run is blocked.',receipt) from None
        try:
            Draft202012Validator(schema).validate(value)
            value=restore_artifact(role,value,reply)
        except (ValidationError,ValueError):
            receipt['completed']=False
            raise ProviderError('The completed model response did not satisfy its response contract. This run is blocked.',receipt) from None
        return value,receipt


def configured_provider(project,persistence=None):
    """Only Anthropic credentials are accepted; never expose them to the browser."""
    settings={};path=Path(project)/'.env'
    if path.is_file():
        for line in path.read_text().splitlines():
            key,sep,value=line.partition('=')
            if sep and key.strip() in ('ANTHROPIC_API_KEY','AUDIT_MODEL','AUDIT_API_BUDGET_USD'):
                settings[key.strip()]=value.strip().strip('\"\'')
    key=os.environ.get('ANTHROPIC_API_KEY') or settings.get('ANTHROPIC_API_KEY')
    model=os.environ.get('AUDIT_MODEL') or settings.get('AUDIT_MODEL') or 'claude-haiku-5-5'
    budget_path=Path(os.environ.get('AUDIT_DATA_DIR',str(Path(project)/'.local/runs'))).parent/'api-budget.json'
    limit=os.environ.get('AUDIT_API_BUDGET_USD') or settings.get('AUDIT_API_BUDGET_USD') or '3.00'
    return AnthropicProvider(key,model,budget=ApiBudget(budget_path,limit,persistence=persistence)) if key else None
