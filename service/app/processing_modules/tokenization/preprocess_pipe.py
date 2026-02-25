from .token_strategy import TokenizationStrategy
from .tokenizer_registry import get_tokenizer
from .stopwords_registry import get_stopwords
from bookService.service.app.corpus import load_raw_text, load_tokens, save_tokens, tokens_exist
import string
import re


def build_tokens(doc_id, strategy: TokenizationStrategy):
    text = load_raw_text(doc_id)
    clean = preprocess(text, strategy)
    tokens = tokenize(clean, strategy)

    save_tokens(doc_id, strategy, tokens)
    return tokens

def preprocess(text: str, strategy: TokenizationStrategy) -> str:
    if strategy.lowercase:
        text = lowercase(text)

    if strategy.special_char_pattern:
        text = remove_special_chars(text, strategy.special_char_pattern)

    if strategy.remove_punctuation:
        text = remove_punctuation(text)

    return text


def tokenize(text: str, strategy: TokenizationStrategy):
    tokenizer = get_tokenizer(strategy.name)
    tokens = tokenizer(text)

    if strategy.stopword_set:
        stopwords = get_stopwords(strategy.stopword_set)
        tokens = [t for t in tokens if t not in stopwords]

    return tokens


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())

def lowercase(text: str) -> str:
    return text.lower()

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans('', '', string.punctuation))

def remove_special_chars(text: str, pattern: str) -> str:
    return re.sub(pattern, "", text)



if __name__ == "__main__":
    import sys
    strategy = TokenizationStrategy(
        name=sys.argv[2] if len(sys.argv) > 2 else "whitespace",
        version= sys.argv[3] if len(sys.argv) > 3 else "v1",
        lowercase= sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else True,
        remove_punctuation= sys.argv[5].lower() == 'true' if len(sys.argv) > 5 else True,
        extra={}
    )
    build_tokens(sys.argv[1], strategy)