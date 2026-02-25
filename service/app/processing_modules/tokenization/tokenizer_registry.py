TOKENIZERS = {}

def register_tokenizer(name):
    def wrapper(fn):
        TOKENIZERS[name] = fn
        return fn
    return wrapper

def get_tokenizer(name: str):
    return TOKENIZERS.get(name)


@register_tokenizer("whitespace")
def whitespace_tokenizer(text: str):
    return text.split()


