from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # up to bookService/
CORPUS_DIR = BASE_DIR / "corpus" / "raw"
PROCESSED_DIR = BASE_DIR / "corpus" / "processed"
GENERATED_DIR = BASE_DIR / "corpus" / "generated"