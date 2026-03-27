import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from .sectioning_strategy import SectioningStrategy, section_strategy_id, COLLECTION_REGISTRY, SECTIONING_REGISTRY, SUBSECTIONING_REGISTRY
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


#------- registry lookups-------

def list_all_sectioning_strategies() -> dict:
    """
    Returns all registered strategies grouped by type.
    """
    logger.info("Listing all sectioning strategies")

    return {
        "collections": sorted(COLLECTION_REGISTRY.keys()),
        "sections": sorted(SECTIONING_REGISTRY.keys()),
        "subsections": sorted(SUBSECTIONING_REGISTRY.keys()),
    }

def list_collection_strategies() -> list[str]:
    logger.debug("Listing collection strategies")
    return sorted(COLLECTION_REGISTRY.keys())

def list_section_strategies() -> list[str]:
    logger.debug("Listing sectioning strategies")
    return sorted(SECTIONING_REGISTRY.keys())

def list_subsection_strategies() -> list[str]:
    logger.debug("Listing subsection strategies")
    return sorted(SUBSECTIONING_REGISTRY.keys())

def validate_strategy_ids(
    collection_id: str,
    section_id: str,
    subsection_id: str | None = None
):
    """
    Ensures provided strategy IDs exist in registry.
    Raises ValueError if not found.
    """

    if collection_id not in COLLECTION_REGISTRY:
        logger.error(f"Invalid collection strategy: {collection_id}")
        raise ValueError(f"Unknown collection strategy: {collection_id}")

    if section_id not in SECTIONING_REGISTRY:
        logger.error(f"Invalid sectioning strategy: {section_id}")
        raise ValueError(f"Unknown sectioning strategy: {section_id}")

    if subsection_id and subsection_id not in SUBSECTIONING_REGISTRY:
        logger.error(f"Invalid subsection strategy: {subsection_id}")
        raise ValueError(f"Unknown subsection strategy: {subsection_id}")

    logger.debug(
        f"Validated strategies: collection={collection_id}, "
        f"section={section_id}, subsection={subsection_id}"
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
