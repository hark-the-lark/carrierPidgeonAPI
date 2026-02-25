from bookService.service.app.corpus import load_raw_text
from .sectioning_strategy import SectioningStrategy
from .sectioning_registry import SECTIONING_REGISTRY, SUBSECTIONING_REGISTRY
import logging

logger = logging.getLogger("corpus_service")

def build(doc_id: str, strategy: SectioningStrategy):
    """
    Build structured sections for a document using a given sectioning strategy.

    Returns a canonical JSON structure with:
        - Top-level: collection(s)
        - Middle-level: sections
        - Low-level: subsections
    All levels include start_char and end_char.
    """
    text = load_raw_text(doc_id)
    logger.info(f"Building sections for doc_id={doc_id} using strategy={strategy.name} v{strategy.version}")

    # Select top-level section builder and optional subsection builder
    collection_builder = SECTIONING_REGISTRY[strategy.collection_function_id]
    section_builder = SECTIONING_REGISTRY[strategy.sectioning_function_id]
    subsection_builder = (
        SUBSECTIONING_REGISTRY.get(strategy.subsectioning_function_id)
        if strategy.subsectioning_function_id
        else None
    )

    # Build top-level collections
    raw_collections = collection_builder(text, strategy.params)
    canonical_collections = []

    for collection_idx, coll in enumerate(raw_collections):
        coll_entry = {
            "id": collection_idx + 1,
            "title": coll.get("title", f"{strategy.level_names[0]} {collection_idx + 1}"),
            "start_char": coll["start_char"],
            "end_char": coll["end_char"]
        }

        # Build middle-level sections
        middle_sections = coll.get("sections", [])
        section_entries = []
        for section_idx, sec in enumerate(middle_sections):
            sec_entry = {
                "id": section_idx + 1,
                "title": sec.get("title", f"{strategy.level_names[1]} {section_idx + 1}"),
                "start_char": sec["start_char"],
                "end_char": sec["end_char"]
            }

            # Optional low-level subsections
            if subsection_builder and "subsections" in sec:
                subsections_raw = sec["subsections"]
                subsection_entries = []
                for sub_idx, sub in enumerate(subsections_raw):
                    sub_entry = {
                        "id": sub_idx + 1,
                        "title": sub.get("title", f"{strategy.level_names[2]} {sub_idx + 1}"),
                        "start_char": sub["start_char"],
                        "end_char": sub["end_char"]
                    }
                    subsection_entries.append(sub_entry)

                sec_entry[strategy.level_names[2] + "s"] = subsection_entries

            section_entries.append(sec_entry)

        coll_entry[strategy.level_names[1] + "s"] = section_entries
        canonical_collections.append(coll_entry)

    # Return canonical structure
    json = {
        "doc_id": doc_id,
        "strategy": {
            "name": strategy.name,
            "version": strategy.version
        },
        "structure": {
            "level_names": strategy.level_names,
            strategy.level_names[0] + "s": canonical_collections
        }
    }

    return json