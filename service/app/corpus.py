import json
from pathlib import Path
from typing import List, Dict

from .config import CORPUS_DIR
from .config import PROCESSED_DIR

class CorpusNotFound(Exception):
    pass

import logging
logger = logging.getLogger(__name__)

def list_documents() -> List[str]:
    return sorted(
        d.name for d in CORPUS_DIR.iterdir()
        if d.is_dir()
    )


def get_document_path(doc_id: str) -> Path:
    path = CORPUS_DIR / doc_id
    if not path.exists():
        raise CorpusNotFound(f"Document '{doc_id}' not found")
    return path


def load_metadata(doc_id: str) -> Dict:
    path = get_document_path(doc_id) / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_raw_text(doc_id: str) -> str:
    path = get_document_path(doc_id) / "source.txt"
    if not path.exists():
        logger.error(f"Missing source.txt for {doc_id}")
        raise FileNotFoundError("source.txt not found")

    logger.info(f"Loading raw text for {doc_id}")
    return path.read_text(encoding="utf-8")


def list_documents() -> List[str]:
    logger.debug("Discovering documents in corpus")

    docs = []
    for d in CORPUS_DIR.iterdir():
        if d.is_dir():
            docs.append(d.name)

    logger.info(f"Discovered {len(docs)} documents")
    return sorted(docs)


def get_document_path(doc_id: str) -> Path:
    path = CORPUS_DIR / doc_id
    if not path.exists():
        logger.warning(f"Requested unknown document: {doc_id}")
        raise CorpusNotFound(f"Document '{doc_id}' not found")
    return path


def load_chapter_index(doc_id: str) -> Dict:
    path = PROCESSED_DIR / doc_id / "chapters_v1.json"
    if not path.exists():
        raise FileNotFoundError("Chapter index not found")
    return json.loads(path.read_text())


def tokenization_dir(doc_id: str, strategy_id: str) -> Path:
    return (
        PROCESSED_DIR
        / doc_id
        / "tokenization"
        / strategy_id
    )


def tokens_exist(doc_id: str, strategy_id: str) -> bool:
    return (tokenization_dir(doc_id, strategy_id) / "tokens.json").exists()


def load_tokens(doc_id: str, strategy_id: str) -> List[str]:
    logger.info(f"Loading tokens for {doc_id} | strategy={strategy_id}")

    path = tokenization_dir(doc_id, strategy_id) / "tokens.json"
    if not path.exists():
        logger.warning(f"Token file missing for {doc_id} | {strategy_id}")
        raise FileNotFoundError("Tokens not found")
    
    return json.loads(path.read_text())


def save_tokens(doc_id: str, strategy_id: str, tokens: List[str], strategy: dict):
    logger.info(f"Saving tokens for {doc_id} | strategy={strategy_id}")

    out_dir = tokenization_dir(doc_id, strategy_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "tokens.json").write_text(json.dumps(tokens))
    (out_dir / "metadata.json").write_text(
        json.dumps({
            "strategy_id": strategy_id,
            "strategy": strategy
        }, indent=2)
    )

    logger.info(f"Saved {len(tokens)} tokens for {doc_id}")
 
    
def list_tokenizations(doc_id: str):
    base = PROCESSED_DIR / doc_id / "tokenization"
    if not base.exists():
        return []

    results = []
    for d in base.iterdir():
        meta = json.loads((d / "metadata.json").read_text())
        results.append(meta)

    return results

def section_dir(doc_id: str) -> Path:
    return PROCESSED_DIR / doc_id / "sections"


def versions_dir(doc_id: str) -> Path:
    return section_dir(doc_id) / "versions"


def index_path(doc_id: str) -> Path:
    return section_dir(doc_id) / "index.json"


def sections_canonical_path(doc_id: str) -> Path:
    return section_dir(doc_id) / "canonical.json"