from fastapi import FastAPI, HTTPException
from typing import List

from service.app.corpus import (
    list_documents,
    load_metadata,
    load_raw_text,
    CorpusNotFound,
)
from .models import DocumentInfo

import logging
import json
from pathlib import Path
from service.app.logging import setup_logging
from service.app.config import CORPUS_DIR, GENERATED_DIR
from service.processing_modules.tokenization.token_strategy import TokenizationStrategy, strategy_id as compute_strategy_id
from service.processing_modules.tokenization.service import get_or_build_tokens
from service.processing_modules.sectioning.service import (
    get_canonical_sections,
    list_section_versions,
    get_section_version,
    build_and_store_sections,
    promote_to_canonical
)
from service.processing_modules.sectioning.sectioning_strategy import SectioningStrategy

from service.app.corpus import list_documents, load_metadata, get_document_path, load_chapter_index, list_tokenizations
from service.app.models import DocumentSummary, SectionBuildRequest, CorpusBuildRequest, CorpusBuildResponse, CorpusMetadata, compute_corpus_id
from typing import List
from datetime import datetime

setup_logging()
logger = logging.getLogger("corpus_service")


app = FastAPI(
    title="Local Corpus Service",
    version="0.1.0",
)


@app.on_event("startup")
def validate_corpus():
    if not CORPUS_DIR.exists():
        raise RuntimeError(f"Corpus directory not found: {CORPUS_DIR}")

@app.on_event("startup")
def startup():
    logger.info("Starting corpus service")
    logger.info(f"Using corpus directory: {CORPUS_DIR}")

    if not CORPUS_DIR.exists():
        logger.error("Corpus directory does not exist")
        raise RuntimeError(f"Corpus directory not found: {CORPUS_DIR}")

    logger.info("Corpus directory validated")



@app.get("/documents", response_model=List[DocumentSummary])
def list_available_documents():
    logger.info("Listing available documents")

    docs = []
    for doc_id in list_documents():
        path = get_document_path(doc_id)
        has_raw = (path / "source.txt").exists()

        docs.append(
            DocumentSummary(
                id=doc_id,
                has_raw=has_raw,
                metadata=load_metadata(doc_id),
            )
        )

    logger.info(f"Returned {len(docs)} documents")
    return docs



@app.get("/documents/{doc_id}/raw")
def get_raw_text(doc_id: str):
    logger.info(f"Fetching raw text for {doc_id}")

    try:
        text = load_raw_text(doc_id)
    except CorpusNotFound:
        logger.warning(f"Document not found: {doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    except FileNotFoundError:
        logger.error(f"source.txt missing for {doc_id}")
        raise HTTPException(status_code=500, detail="source.txt missing")

    return {"id": doc_id, "text": text}



# --- canonical sections endpoints ---

@app.get("/documents/{doc_id}/sections")
def get_canonical_sections_endpoint(doc_id: str):
    """
    Return the entire canonical section JSON for the document.
    """
    try:
        sections = get_canonical_sections(doc_id)
        logger.info(f"Canonical sections retrieved for doc_id={doc_id}")
        return sections
    except FileNotFoundError:
        logger.warning(f"No canonical sections found for doc_id={doc_id}")
        raise HTTPException(status_code=404, detail="Canonical sections not found")


@app.get("/documents/{doc_id}/sections/{level1}/{index1}")
@app.get("/documents/{doc_id}/sections/{level1}/{index1}/{level2}/{index2}")
@app.get("/documents/{doc_id}/sections/{level1}/{index1}/{level2}/{index2}/{level3}/{index3}")
def get_section_slice(doc_id: str, level1: str, index1: int, 
                      level2: str = None, index2: int = None,
                      level3: str = None, index3: int = None) -> dict:
    """
    Traverse the canonical section JSON for a document and return the requested section slice.

    Args:
        doc_id (str): Document ID
        level1, level2, level3 (str): Level names (book, chapter, paragraph)
        index1, index2, index3 (int): 0-based indices for the respective levels

    Returns:
        dict: The section slice JSON
    """
    try:
        canonical = get_canonical_sections(doc_id)
        logger.info(f"Loaded canonical sections for {doc_id}")
    except FileNotFoundError:
        logger.warning(f"No canonical sections found for {doc_id}")
        raise HTTPException(status_code=404, detail="Canonical section not found")

    # Start traversal at 'structure'
    structure = canonical.get("structure")
    if not structure:
        logger.warning(f"'structure' key missing in canonical JSON for {doc_id}")
        raise HTTPException(status_code=500, detail="'structure' key missing in canonical JSON")

    # --- Level 1 ---
    top_level_items = structure.get(level1)
    if not top_level_items:
        logger.warning(f"Top-level section not found: doc_id={doc_id}, level1={level1}[{index1}]")
        raise HTTPException(status_code=404, detail=f"Top-level {level1} not found")

    if index1 >= len(top_level_items) or index1 < 0:
        logger.warning(f"Index out of bounds for {level1}: doc_id={doc_id}, index={index1}")
        raise HTTPException(status_code=404, detail=f"{level1} index out of range")
    
    section = top_level_items[index1]
    logger.info(f"Fetched {level1} index {index1} for {doc_id}")

    # --- Level 2 ---
    if level2 and index2 is not None:
        second_level_items = section.get(level2)
        if not second_level_items:
            logger.warning(f"Second-level section not found: doc_id={doc_id}, level1={level1}[{index1}], level2={level2}[{index2}]")
            raise HTTPException(status_code=404, detail=f"{level2} not found in {level1}")
        
        if index2 >= len(second_level_items) or index2 < 0:
            logger.warning(f"Index out of bounds for {level2}: doc_id={doc_id}, index={index2}")
            raise HTTPException(status_code=404, detail=f"{level2} index out of range")
        
        section = second_level_items[index2]
        logger.info(f"Fetched {level2} index {index2} for {doc_id}")

    # --- Level 3 ---
    if level3 and index3 is not None:
        third_level_items = section.get(level3)
        if not third_level_items:
            logger.warning(f"Third-level section not found: doc_id={doc_id}, level1={level1}[{index1}], level2={level2}[{index2}], level3={level3}[{index3}]")
            raise HTTPException(status_code=404, detail=f"{level3} not found in {level2}")
        
        if index3 >= len(third_level_items) or index3 < 0:
            logger.warning(f"Index out of bounds for {level3}: doc_id={doc_id}, index={index3}")
            raise HTTPException(status_code=404, detail=f"{level3} index out of range")
        
        section = third_level_items[index3]
        logger.info(f"Fetched {level3} index {index3} for {doc_id}")

    return section


# --- dynamic text slicing endpoint ---

@app.get("/documents/{doc_id}/{start_char}/{end_char}/text")
def get_text_slice(doc_id: str, start_char: int, end_char: int):
    """
    Return a slice of raw text between start_char and end_char.
    """
    try:
        text = load_raw_text(doc_id)
    except FileNotFoundError:
        logger.warning(f"Raw text not found for doc_id={doc_id}")
        raise HTTPException(status_code=404, detail="Document source not found")

    if start_char < 0 or end_char > len(text) or start_char >= end_char:
        logger.warning(
            f"Invalid text slice requested: doc_id={doc_id}, "
            f"start_char={start_char}, end_char={end_char}"
        )
        raise HTTPException(status_code=400, detail="Invalid character range")

    logger.info(
        f"Text slice retrieved: doc_id={doc_id}, "
        f"start_char={start_char}, end_char={end_char}, length={end_char-start_char}"
    )

    return {
        "doc_id": doc_id,
        "start_char": start_char,
        "end_char": end_char,
        "text": text[start_char:end_char]
    }


@app.get("/documents/{doc_id}/tokens")
def list_tokens(doc_id: str):
    return list_tokenizations(doc_id)


@app.get("/documents/{doc_id}/tokens/{strategy_id}")
def get_tokens(doc_id: str, strategy_id: str):
    path = (
        Path("../corpus/processed")
        / doc_id
        / "tokenization"
        / strategy_id
        / "tokens.json"
    )

    if not path.exists():
        raise HTTPException(status_code=404, detail="Tokenization not found")

    return json.loads(path.read_text())


@app.post("/documents/{doc_id}/tokens")
def build_tokens(doc_id: str, strategy: TokenizationStrategy):
    sid = compute_strategy_id(strategy)
    logger.info(f"Token request for {doc_id} using strategy {sid}")

    tokens, status = get_or_build_tokens(doc_id, strategy)

    logger.info(f"Tokenization {status} for {doc_id} ({len(tokens)} tokens)")

    return {
        "strategy_id": sid,
        "status": status,
        "num_tokens": len(tokens),
        "tokens": tokens,
    }

@app.get("/documents/{doc_id}/sections")
def get_sections(doc_id: str):
    try:
        return get_canonical_sections(doc_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No canonical section structure found"
        )


@app.get("/documents/{doc_id}/sections/versions")
def list_section_versions_endpoint(doc_id: str):
    return list_section_versions(doc_id)


@app.get("/documents/{doc_id}/sections/versions/{version_id}")
def get_section_version_endpoint(doc_id: str, version_id: str):
    try:
        return get_section_version(doc_id, version_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Section version not found"
        )


@app.post("/documents/{doc_id}/sections/build")
def build_sections_endpoint(doc_id: str, request: SectionBuildRequest):
    logger.info(f"Section build requested for {doc_id}")

    try:
        strategy = SectioningStrategy(**request.strategy)
    except Exception as e:
        logger.warning(f"Invalid section strategy for {doc_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid sectioning strategy: {e}")

    try:
        result = build_and_store_sections(
            doc_id,
            strategy,
            promote_to_canonical=request.promote_to_canonical,
        )
        logger.info(f"Section build complete for {doc_id}")
        return result
    except FileNotFoundError:
        logger.warning(f"Document not found during section build: {doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")


@app.post("/documents/{doc_id}/sections/promote/{version_id}")
def promote_section_version(doc_id: str, version_id: str):
    try:
        promote_to_canonical(doc_id, version_id)
        return {
            "doc_id": doc_id,
            "canonical_version": version_id,
            "status": "promoted"
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Section version not found"
        )

@app.post("/corpus/build", response_model=CorpusBuildResponse)
def build_corpus(request: CorpusBuildRequest):

    logger.info("Starting corpus build")

    processor = request.processing_strategy

    processed_texts = []
    fingerprint_parts = []
    total_characters = 0

    for doc_slice in request.documents:
        logger.info(
            f"Reading document slice: {doc_slice.doc_id} "
            f"[{doc_slice.start_char}:{doc_slice.end_char}]"
        )

        raw_text = compute_strategy_id(doc_slice.doc_id)

        if doc_slice.end_char > len(raw_text):
            raise HTTPException(
                status_code=400,
                detail=f"Slice exceeds document length for {doc_slice.doc_id}"
            )

        slice_text = raw_text[doc_slice.start_char:doc_slice.end_char]

        processed = processor(slice_text)
        processed_texts.append(processed)

        total_characters += len(processed)

        fingerprint_parts.append(
            f"{doc_slice.doc_id}:{doc_slice.start_char}:{doc_slice.end_char}:{request.processing_strategy}"
        )

    fingerprint = "|".join(fingerprint_parts)
    corpus_id = compute_corpus_id(fingerprint)

    metadata = CorpusMetadata(
        corpus_id=corpus_id,
        documents=request.documents,
        processing_strategy=request.processing_strategy,
        created_at=datetime.utcnow(),
        total_characters=total_characters,
    )

    if request.persist:
        output_path = GENERATED_DIR / f"{corpus_id}.json"

        logger.info(f"Persisting corpus to {output_path}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": metadata.dict(),
                    "corpus": processed_texts,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    logger.info(f"Corpus build complete: {corpus_id}")

    return CorpusBuildResponse(
        metadata=metadata,
        corpus=processed_texts,
    )