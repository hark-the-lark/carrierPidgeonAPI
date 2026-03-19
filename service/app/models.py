from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
import hashlib

from service.processing_modules.tokenization.token_strategy import TokenizationStrategy


class DocumentInfo(BaseModel):
    id: str
    metadata: Dict


class DocumentSummary(BaseModel):
    id: str
    has_raw: bool
    metadata: Dict

class SectionBuildRequest(BaseModel):
    strategy: Dict
    promote_to_canonical: bool = False



class DocumentSlice(BaseModel):
    doc_id: str
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)


class CorpusBuildRequest(BaseModel):
    documents: List[DocumentSlice]
    processing_strategy: TokenizationStrategy
    persist: bool = True


class CorpusMetadata(BaseModel):
    corpus_id: str
    documents: List[DocumentSlice]
    processing_strategy: str
    created_at: datetime
    total_characters: int


class CorpusBuildResponse(BaseModel):
    metadata: CorpusMetadata
    corpus: List[str]


def compute_corpus_id(fingerprint: str) -> str:
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
