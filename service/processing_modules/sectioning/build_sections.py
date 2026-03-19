from service.app.corpus import load_raw_text
from .sectioning_strategy import SectioningStrategy
from .sectioning_registry import (
    SECTIONING_REGISTRY,
    SUBSECTIONING_REGISTRY,
    COLLECTION_REGISTRY
)
import logging

logger = logging.getLogger("corpus_service")


def build(doc_id: str, strategy: SectioningStrategy):

    logger.info(f"Starting section build | doc={doc_id}")

    text = load_raw_text(doc_id)

    # ---------- Resolve builders ----------

    collection_builder = None
    if strategy.collection_function_id:
        collection_builder = COLLECTION_REGISTRY.get(
            strategy.collection_function_id
        )

    section_builder = SECTIONING_REGISTRY[strategy.sectioning_function_id]

    subsection_builder = (
        SUBSECTIONING_REGISTRY.get(strategy.subsectioning_function_id)
        if strategy.subsectioning_function_id
        else None
    )

    logger.info(f"Collection builder: {strategy.collection_function_id}")
    logger.info(f"Section builder: {strategy.sectioning_function_id}")
    logger.info(f"Subsection builder: {strategy.subsectioning_function_id}")

    # ---------- Build collections ----------

    if collection_builder:
        collections = collection_builder(text, strategy.params)
    else:
        logger.info("No collection strategy provided, using full text")
        collections = [{
            "title": "Full Text",
            "start_char": 0,
            "end_char": len(text)
        }]

    collection_results = []

    # ---------- Iterate collections ----------

    for cid, col in enumerate(collections, start=1):

        logger.info(f"Processing collection {cid}")

        collection_entry = {
            "id": cid,
            "title": col.get("title", f"Collection {cid}"),
            "start_char": col["start_char"],
            "end_char": col["end_char"]
        }

        block_text = text[col["start_char"]:col["end_char"]]

        raw_sections = section_builder(block_text, strategy.params)

        logger.info(f"Found {len(raw_sections)} sections in collection {cid}")

        sections = []

        for sid, sec in enumerate(raw_sections, start=1):

            sec_start = col["start_char"] + sec["start_char"]
            sec_end = col["start_char"] + sec["end_char"]

            section_entry = {
                "id": sid,
                "title": sec.get("title"),
                "start_char": sec_start,
                "end_char": sec_end
            }

            # ---------- Subsections ----------

            if subsection_builder:
                logger.info(f"Building subsections for section {sid}")

                subsections = subsection_builder(
                    text,
                    section_entry,
                    strategy.params
                )

                logger.info(f"Built {len(subsections)} subsections")

                section_entry[
                    strategy.level_names[2] + "s"
                ] = subsections

            sections.append(section_entry)

        collection_entry[
            strategy.level_names[1] + "s"
        ] = sections

        collection_results.append(collection_entry)

    result = {
        "doc_id": doc_id,
        "strategy": {
            "collection_strategy": strategy.collection_function_id,
            "section_strategy": strategy.sectioning_function_id,
            "subsection_strategy": strategy.subsectioning_function_id
        },
        "structure": {
            "level_names": strategy.level_names,
            strategy.level_names[0] + "s": collection_results
        }
    }

    logger.info(f"Completed section build | doc={doc_id}")

    return result