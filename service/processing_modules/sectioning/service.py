import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from .sectioning_strategy import SectioningStrategy, section_strategy_id
from .build_sections import build as build_sections
from service.app.corpus import section_dir, index_path, versions_dir, sections_canonical_path
from service.app.logging import logging, setup_logging

logger = logging.getLogger(__name__)

# ---------- read APIs ----------

def get_canonical_sections(doc_id: str) -> dict:
    path = sections_canonical_path(doc_id)
    if not path.exists():
        raise FileNotFoundError("No canonical sections defined")

    return json.loads(path.read_text(encoding="utf-8"))


def list_section_versions(doc_id: str) -> dict:
    path = index_path(doc_id)
    if not path.exists():
        return {"canonical": None, "available": []}

    return json.loads(path.read_text(encoding="utf-8"))


def get_section_version(doc_id: str, version_id: str) -> dict:
    path = versions_dir(doc_id) / f"{version_id}.json"
    if not path.exists():
        raise FileNotFoundError("Section version not found")

    return json.loads(path.read_text(encoding="utf-8"))


# ---------- write APIs ----------

def build_and_store_sections(
    doc_id: str,
    strategy: SectioningStrategy,
    promote_to_canonical: bool = False
) -> dict:

    section_dir(doc_id).mkdir(parents=True, exist_ok=True)
    versions_dir(doc_id).mkdir(parents=True, exist_ok=True)

    sid = f"{section_strategy_id(strategy)}"
    logger.info(f"Building sections | doc={doc_id} | strategy={sid}")


    structure = build_sections(doc_id, strategy)
    logger.info(f"Built sections for {doc_id}")
    version_path = versions_dir(doc_id) / f"{sid}.json"
    version_path.write_text(
        json.dumps(structure, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    meta = {
        "id": sid,
        "strategy": {
            "collection_strategy": strategy.collection_function_id,
            "section_strategy": strategy.sectioning_function_id,
            "subsection_strategy": strategy.subsectioning_function_id
        },
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    _update_index(doc_id, meta, promote_to_canonical)

    if promote_to_canonical:
        sections_canonical_path(doc_id).write_text(
            json.dumps(structure, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info(f"Promoted {sid} to canonical for {doc_id}")
        
    return {
        "version_id": sid,
        "canonical": promote_to_canonical
    }


def promote_to_canonical(doc_id: str, version_id: str):
    src = versions_dir(doc_id) / f"{version_id}.json"
    if not src.exists():
        raise FileNotFoundError("Section version not found")

    sections_canonical_path(doc_id).write_text(
        src.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    index = list_section_versions(doc_id)
    index["canonical"] = version_id

    index_path(doc_id).write_text(
        json.dumps(index, indent=2),
        encoding="utf-8"
    )


# ---------- internal ----------

def _update_index(doc_id: str, meta: dict, canonical: bool):
    path = index_path(doc_id)

    if path.exists():
        index = json.loads(path.read_text())
    else:
        index = {"canonical": None, "available": []}

    index["available"].append(meta)

    if canonical:
        index["canonical"] = meta["id"]

    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
