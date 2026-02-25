STOPWORD_SETS = {}

def register_stopwords(name: str):
    def wrapper(words: set[str]):
        STOPWORD_SETS[name] = words
        return words
    return wrapper


def get_stopwords(name: str):
    return STOPWORD_SETS.get(name)

@register_stopwords("english_v1")
def _():
    return {"the", "and", "of", "to"}

