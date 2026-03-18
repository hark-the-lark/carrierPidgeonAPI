from carrierPidgeonAPI.service.app.corpus import load_raw_text
from .sectioning_strategy import SectioningStrategy
from .sectioning_registry import SECTIONING_REGISTRY, SUBSECTIONING_REGISTRY, COLLECTION_REGISTRY
import logging

logger = logging.getLogger("corpus_service")
def build(doc_id: str, strategy: SectioningStrategy):

    text = load_raw_text(doc_id)

    collection_builder = COLLECTION_REGISTRY[strategy.collection_function_id]
    section_builder = SECTIONING_REGISTRY[strategy.sectioning_function_id]

    subsection_builder = (
        SUBSECTIONING_REGISTRY.get(strategy.subsectioning_function_id)
        if strategy.subsectioning_function_id
        else None
    )

    collections = collection_builder(text, strategy.params)

    collection_results = []

    for cid, col in enumerate(collections, start=1):

        collection_entry = {
            "id": cid,
            "title": col.get("title", f"Collection {cid}"),
            "start_char": col["start_char"],
            "end_char": col["end_char"]
        }

        block_text = text[col["start_char"]:col["end_char"]]

        raw_sections = section_builder(block_text, strategy.params)

        sections = []

        for sid, sec in enumerate(raw_sections, start=1):

            # adjust offsets relative to whole text
            sec_start = col["start_char"] + sec["start_char"]
            sec_end = col["start_char"] + sec["end_char"]

            section_entry = {
                "id": sid,
                "title": sec.get("title"),
                "start_char": sec_start,
                "end_char": sec_end
            }

            if subsection_builder:

                subsections = subsection_builder(
                    text,
                    section_entry,
                    strategy.params
                )

                section_entry[strategy.level_names[2] + "s"] = subsections

            sections.append(section_entry)

        collection_entry[strategy.level_names[1] + "s"] = sections
        collection_results.append(collection_entry)

    return {
        "doc_id": doc_id,
        "strategy": {
            "name": strategy.name,
            "version": strategy.version
        },
        "structure": {
            "level_names": strategy.level_names,
            strategy.level_names[0] + "s": collection_results
        }
    }