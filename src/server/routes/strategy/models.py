from pydantic import BaseModel


class StrategyCreate(BaseModel):
    prompt: str