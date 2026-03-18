from datetime import datetime
import json
import hashlib
from pathlib import Path


from .token_strategy import TokenizationStrategy, strategy_id
from .preprocess_pipe import preprocess, tokenize
from carrierPidgeonAPI.service.app.corpus import load_raw_text, save_tokens, load_tokens, tokens_exist
from carrierPidgeonAPI.service.app.logging import logging, setup_logging

from bookService.service.app.config import PROCESSED_DIR

setup_logging()
logger = logging.getLogger(__name__)

def tokenization_dir(doc_id: str, strategy: TokenizationStrategy) -> Path:
    return (
        PROCESSED_DIR
        / doc_id
        / "tokenization"
        / strategy_id(strategy)
    )


def get_or_build_tokens(doc_id: str, strategy: TokenizationStrategy):
    sid = strategy_id(strategy)

    logger.info(f"Tokenization requested | doc={doc_id} | strategy={sid}")

    if tokens_exist(doc_id, sid):
        logger.info(f"Token cache hit | doc={doc_id} | strategy={sid}")
        return load_tokens(doc_id, sid), "cache_hit"

    logger.info(f"Building tokens | doc={doc_id} | strategy={sid}")

    text = load_raw_text(doc_id)
    clean = preprocess(text, strategy)
    tokens = tokenize(clean, strategy)

    logger.debug(f"Built {len(tokens)} tokens")

    save_tokens(doc_id, sid, tokens, strategy.dict())

    logger.info(f"Token build complete | doc={doc_id}")

    return tokens, "built"