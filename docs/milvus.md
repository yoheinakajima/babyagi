# How to setup

## Setup

1. Install milvus:

```bash
pip -r extensions/requirements.txt
```

2. Configure the following environment variables:

Uncomment the following lines in .env file, replace them with your own config if necessary:

```bash
MILVUS_URI=http://localhost:19530
MILVUS_VECTOR_FIELD=embedding
RESULTS_STORE_NAME=baby_agi_test_table
```