from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import hashlib

class SectioningStrategy(BaseModel):

    # Structural contract
    level_names: List[str] = Field(
        description="Hierarchical structure, e.g. ['book', 'section', 'paragraph']"
    )

    # Algorithm selection
    collection_function_id: str
    sectioning_function_id: str
    subsectioning_function_id: Optional[str] = None

    # Hyperparameters (passed through verbatim)
    params: Dict[str, Any] = Field(default_factory=dict)


def section_strategy_id(strategy: SectioningStrategy) -> str:
    payload = json.dumps(strategy.model_dump(), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]
