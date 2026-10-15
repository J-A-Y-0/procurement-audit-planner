from datetime import date as Date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Input(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class CreateRun(Input):
    title:str=Field(min_length=1,max_length=100)
    mode:Literal['live']='live'

class RiskDecision(Input):
    id:str=Field(pattern=r'^R-\d{2}$')
    decision:Literal['approve','amend','reject']
    comment:str=Field(default='',max_length=2000)
    in_scope:bool

class Human(Input):
    expected_version:int=Field(ge=1)
    reviewer:str=Field(min_length=1,max_length=100)
    date:Date

    @field_validator('reviewer')
    @classmethod
    def one_line(cls,value):
        if '\n' in value or '\r' in value:
            raise ValueError('Reviewer must be a single line.')
        return value

class Scope(Human):
    decisions:list[RiskDecision]=Field(min_length=1,max_length=30)

class Signoff(Human):
    decision:Literal['sign_off','return']
    comment:str=Field(default='',max_length=2000)

    @model_validator(mode='after')
    def return_reason(self):
        if self.decision=='return' and not self.comment.strip():
            raise ValueError('Returning the plan requires a comment explaining the revision needed.')
        return self
