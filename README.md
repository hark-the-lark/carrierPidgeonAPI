# Carrier Pidgeon API

A modular, local-first text corpus service for ingesting, structuring, processing, and serving literary documents.

---

## 🧠 Project Overview

Carrier Pidgeon API is designed as a flexible backend for working with raw text corpora. It provides:

- Raw document storage
- Structured sectioning (books, chapters, paragraphs, etc.)
- Tokenization pipelines
- Corpus generation for downstream tasks (e.g., vectorization, training)

The system is built with a strong emphasis on:

- **Deterministic processing**
- **Reproducibility**
- **Extensibility via registries**
- **Separation of concerns between storage, processing, and API layers**



## Directory Structure
carrierPidgeonAPI/
│
├── corpus/
│ ├── raw/
│ │ └── {document_id}/
│ │ ├── source.txt
│ │ └── metadata.json
│ │
│ ├── processed/
│ │ └── {document_id}/
│ │ ├── tokens/
│ │ │ └── {strategy_id}.json
│ │ ├── sections/
│ │ │ ├── versions/
│ │ │ │ └── {strategy_id}.json
│ │ │ └── canonical.json
│ │
│ └── generated/
│ └── {corpus_hash}.json
│
├── service/
│ ├── app/
│ │ ├── main.py
│ │ ├── corpus.py
│ │ ├── models.py
│ │ ├── config.py
│ │ ├── logging.py
│ │
│ ├── processing_modules/
│ │ ├── tokenization/
│ │ └── sectioning/
│ │
│ └── scripts/
│ ├── build_sections.sh
│ └── promote_to_canonical.sh
│
├── dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.sh


---

## 📚 Corpus Design & Ontology

### Raw Corpus (`corpus/raw/`)

Each document is stored as:
{document_id}/
├── source.txt # full raw text
└── metadata.json # optional metadata

---

### Processed Corpus (`corpus/processed/`)

#### 🔹 Tokenization

Multiple tokenization strategies are cached:
tokens/{strategy_id}.json

Each strategy is deterministic and reproducible.

---

#### 🔹 Sectioning

Sectioning produces structured representations of a document.

- Multiple versions can exist:
sections/versions/{strategy_id}.json

- One version can be promoted as canonical:
sections/canonical.json

---

### 🧪 Generated Corpora (`corpus/generated/`)

Built dynamically from slices of documents:
{corpus_hash}.json

Each corpus includes:

- Source document slices
- Processing strategy
- Metadata for reproducibility

---

## 🧩 Processing Modules

Processing modules are **pluggable and registry-based**.

---

### 🔤 Tokenization Module

Handles:

- Preprocessing (normalization, stopword removal, etc.)
- Token generation

Key files:
- `preprocess_pipe.py`
- `tokenizer_registry.py`
- `token_strategy.py`
- `service.py`

---

### 📖 Sectioning Module

Handles hierarchical document structure:

- Collection → Section → Subsection
- Example: Book → Chapter → Paragraph

Key concepts:

- **Strategies define structure**
- **Registries define implementation**

Key files:
- `sectioning_strategy.py`
- `sectioning_registry.py`
- `build_sections.py`
- `service.py`

---

## 🌐 API Overview

The API is built with FastAPI and exposes endpoints for:

---

### 📄 Documents

#### List documents
GET /documents

#### Get raw text
GET /documents/{doc_id}/raw


---

### 🔤 Tokenization

#### List tokenizations
GET /documents/{doc_id}/tokens

#### Get tokens
GET /documents/{doc_id}/tokens/{strategy_id}

#### Build tokens
POST /documents/{doc_id}/tokens


---

### 📖 Sectioning

#### Get canonical sections
GET /documents/{doc_id}/sections

#### List section versions
GET /documents/{doc_id}/sections/versions


#### Get specific version
GET /documents/{doc_id}/sections/versions/{version_id}


#### Build sections
POST /documents/{doc_id}/sections/build


#### Promote to canonical
POST /documents/{doc_id}/sections/promote/{version_id}


---

# 🧩 2. Sectioning Pipeline Flow


### ✂️ Raw Text Slicing

#### Get arbitrary slice of text
GET /documents/{doc_id}/{start_char}/{end_char}/text

---

### 🧪 Corpus Builder

#### Build corpus from slices
POST /corpus/build

Example request:


{
  "documents": [
    {
      "doc_id": "pride_and_prejudice",
      "start_char": 0,
      "end_char": 5000
    }
  ],
  "processing_strategy": "basic_normalization_v1",
  "persist": true
}


---

# 🧪 3. Corpus Builder Flow

This is especially important since it's your bridge to vectorization later.


⚙️ Running the API
Local (Recommended for Development)
./run.sh
then access
http://127.0.0.1:8000

Docker

Build and run:

docker compose up --build

The container mounts your local corpus/ directory, so:

Writes persist locally

You can inspect outputs directly

🧪 Example Usage
Build sections
curl -X POST http://127.0.0.1:8000/documents/pride_and_prejudice/sections/build \
-H "Content-Type: application/json" \
-d '{
  "strategy": {
    "name": "classic_sections",
    "version": "v2",
    "level_names": ["book", "chapter", "paragraph"],
    "collection_function_id": "single_collection_v1",
    "sectioning_function_id": "classic_chapters_v2",
    "subsectioning_function_id": "blankline_paragraphs_v1",
    "params": {}
  },
  "promote_to_canonical": true
}'

Build corpus
curl -X POST http://127.0.0.1:8000/corpus/build \
-H "Content-Type: application/json" \
-d '{
  "documents": [
    {
      "doc_id": "pride_and_prejudice",
      "start_char": 0,
      "end_char": 5000
    }
  ],
  "processing_strategy": "basic_normalization_v1",
  "persist": true
}'

🧭 Design Philosophy

This system is intentionally designed to:

Be local-first (no required external services)

Support multiple processing strategies simultaneously

Keep raw data immutable

Allow evolution toward more advanced systems (vector DBs, ML pipelines)

🚧 Future Directions

Vectorization service (separate microservice)

Corpus versioning + lineage tracking

Database-backed storage

Kubernetes-based deployment

Streaming / chunked processing

📝 Notes

The current corpus structure is subject to change

Processed artifacts are considered derived and replaceable

Canonical sectioning should be treated as best-known structure, not ground truth


---
