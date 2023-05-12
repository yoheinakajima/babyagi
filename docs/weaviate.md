# How to setup

## Setup

1. Install weaviate client:

```bash
pip -r extensions/requirements.txt
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

If using Embedded Weaviate, configure it like:

```bash
WEAVIATE_USE_EMBEDDED=true
# WEAVIATE_URL=
# WEAVIATE_API_KEY=
```

If using a WCS (Weaviate Cloud Service) instance

```bash
# WEAVIATE_USE_EMBEDDED=true
WEAVIATE_URL=https://your-endpoint.weaviate.network  # Replace with your URL
WEAVIATE_API_KEY=YOUR-WEAVIATE-API-KEY  # If authentication is enabled
```

Follow step 4 onwards in main README

## Using BabyAGI with Docker & Weaviate

If you want to use BabyAGI with Docker, and use Weaviate as the object store, you should also:

- Edit `requirements.txt` to add:
```bash
weaviate-client>=3.16.1
```
- And in case you are running Weaviate through Docker-Compose, change its port so it is different from that used by babyAgi. For example, specify in `.env`:

```bash
WEAVIATE_URL=http://localhost:8099
```

And edit Weaviate's Docker-Compose file to change the ports as below

```
services:
  weaviate:
    command:
    - --host
    - 0.0.0.0
    - --port
    - '8099'  # Specify different port to avoid conflict
    - --scheme
    - http
    image: semitechnologies/weaviate:1.19.2
    ports:
    - 8099:8099
```
