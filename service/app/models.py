from pydantic import BaseModel
from typing import Dict
from pydantic import BaseModel
from typing import Dict

class DocumentInfo(BaseModel):
    id: str
    metadata: Dict



class DocumentSummary(BaseModel):
    id: str
    has_raw: bool
    metadata: Dict


from pydantic import BaseModel
from typing import List, Optional, Dict

class SectionBuildRequest(BaseModel):
    strategy: Dict
    promote_to_canonical: bool = False
