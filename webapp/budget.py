"""Persistent conservative reservation for this single-process API service."""
import json
import math
import threading
import uuid
from pathlib import Path

class BudgetError(RuntimeError):pass

class ApiBudget:
    def __init__(self,path,limit_usd,persistence=None):
        self.path=Path(path);self.limit=math.floor(float(limit_usd)*1000000)
        self.lock=threading.RLock()
        self.persistence=persistence
        if self.limit<=0:raise BudgetError('API budget must be positive.')

    def read(self):
        if self.persistence:
            raw=self.persistence.get('api-budget')
            return json.loads(raw) if raw is not None else {'committed_micro_usd':0,'reservations':{}}
        return json.loads(self.path.read_text()) if self.path.exists() else {'committed_micro_usd':0,'reservations':{}}

    def save(self,state):
        if self.persistence:
            self.persistence.put('api-budget',json.dumps(state).encode())
            return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state,indent=2)+'\n');temporary.replace(self.path)

    def reserve(self,model,input_tokens,max_output):
        if model!='claude-haiku-5-5':raise BudgetError('This budget configuration permits only Claude Haiku 5.5.')
        # Count estimates may differ slightly from billed tokens. Use a 10% margin,
        # the higher tariff if near its threshold, and the full output allowance.
        upper=math.ceil(input_tokens*1.1)+100
        input_rate,output_rate=(.1,.5) if upper<=100000 else (.5,2.5)
        reserve=math.ceil(upper*input_rate+max_output*output_rate)
        with self.lock:
            state=self.read()
            if state['committed_micro_usd']+sum(state['reservations'].values())+reserve>self.limit:
                raise BudgetError('The application API budget cannot cover another request. No generation request was sent; ask the operator to review usage.')
            token=uuid.uuid4().hex;state['reservations'][token]=reserve;self.save(state)
            return token

    def settle(self,token,usage):
        # Release a reservation only after completed generation reports usage.
        # Interrupted/uncertain requests retain their full reservation across restarts.
        inputs=usage.get('input_tokens',0)+usage.get('cache_creation_input_tokens',0)+usage.get('cache_read_input_tokens',0)
        input_rate,output_rate=(.1,.5) if inputs<=100000 else (.5,2.5)
        actual=math.ceil(inputs*input_rate+usage.get('output_tokens',0)*output_rate)
        with self.lock:
            state=self.read();state['reservations'].pop(token)
            state['committed_micro_usd']+=actual;self.save(state)
        return actual/1000000
