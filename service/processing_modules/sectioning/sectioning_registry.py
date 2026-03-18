from typing import Callable, Dict
import re

SectionBuilder = Callable[[str, dict], list]
SubsectionBuilder = Callable[[str, dict, dict], list]

COLLECTION_REGISTRY: Dict[str, SectionBuilder] = {}
SECTIONING_REGISTRY: Dict[str, SectionBuilder] = {}
SUBSECTIONING_REGISTRY: Dict[str, SubsectionBuilder] = {}

def register_collection(id: str):
    def decorator(fn: SectionBuilder):
        COLLECTION_REGISTRY[id] = fn
        return fn
    return decorator

def register_sectioning(id: str):
    def decorator(fn: SectionBuilder):
        SECTIONING_REGISTRY[id] = fn
        return fn
    return decorator

def register_subsectioning(id: str):
    def decorator(fn: SubsectionBuilder):
        SUBSECTIONING_REGISTRY[id] = fn
        return fn
    return decorator

@register_collection("single_collection_v1")
def single_collection(text: str, params: dict):
    return [{
        "title": "Full Text",
        "start_char": 0,
        "end_char": len(text)
    }]

@register_sectioning("classic_chapters_v2")
def classic_chapter_sections(text: str, params: dict):
    header_re = re.compile(
        params.get(
            "header_regex",
            r"^(CHAPTER\s+(?:\d+|[IVXLCDM]+)\b.*)$"
        ),
        re.MULTILINE | re.IGNORECASE
    )

    min_chars = params.get("min_chars", 2000)

    headers = [
        {"title": m.group(0).strip(), "start": m.start()}
        for m in header_re.finditer(text)
    ]

    sections = []
    for i, h in enumerate(headers):
        start = h["start"]
        end = headers[i + 1]["start"] if i + 1 < len(headers) else len(text)

        if end - start < min_chars:
            continue

        sections.append({
            "id": len(sections) + 1,
            "title": h["title"],
            "start_char": start,
            "end_char": end
        })

    return sections


@register_subsectioning("blankline_paragraphs_v1")
def paragraph_subsections(text: str, section: dict, params: dict):
    start_char = section["start_char"]
    end_char = section["end_char"]

    block = text[start_char:end_char]
    paras = []
    offset = start_char
    pid = 1

    for chunk in block.split("\n\n"):
        chunk = chunk.strip()
        if not chunk:
            offset += 2
            continue

        s = text.find(chunk, offset)
        e = s + len(chunk)

        paras.append({
            "id": pid,
            "start_char": s,
            "end_char": e
        })

        pid += 1
        offset = e

    return paras
