from pydantic import BaseModel
from typing import Dict
import hashlib
import json


class TokenizationStrategy(BaseModel):
    name: str
    version: str
    lowercase: bool 
    remove_punctuation: bool
    special_char_pattern: str | None = None
    stopword_set: str | None = None
    tokenizer: None | str
    extra: Dict = {}

def strategy_id(strategy: TokenizationStrategy) -> str:
    payload = json.dumps(strategy.dict(), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


