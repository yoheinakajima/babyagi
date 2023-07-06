# How to setup

## Setup

1. Install weaviate client:

```bash
pip install -r extensions/requirements.txt
```

2. Configure the following environment variables:

```bash
TABLE_NAME=BabyAGITableInWeaviate

# Weaviate config
# Uncomment and fill these to switch from local ChromaDB to Weaviate
WEAVIATE_USE_EMBEDDED=true
WEAVIATE_URL=
WEAVIATE_API_KEY=
```
Follow step 4 onwards in main README
