# Tair 

[Tair](https://www.alibabacloud.com/help/en/tair/latest/tairvector) is a cloud native in-memory database service that is developed by Alibaba Cloud. Tair is compatible with open source Redis and provides a variety of data models and enterprise-class capabilities to support your real-time online scenarios. Tair offers a powerful vector extension, processing billions of data vectors and providing a wide range of features, including indexing algorithms, structured attrs and unstructured vector capabilities, real-time updates, distance metrics, scalar filtering. Additionally, Tair offers  SLA commitment for production use。

## Install Requirements

Run the following command to install the tair python client:

```bash
pip3 install tair
```

**Environment Variables:**

| Name                   | Required | Description    | Default     |
|------------------------|----------|----------------|-------------|
| `TAIR_HOST`            | Yes      | Tair host url  | `localhost` |
| `TAIR_PORT`            | Yes      | Tair host port | `6379`      |
| `TAIR_USERNAME`        | Yes      | Tair username  |             |
| `TAIR_PASSWORD`        | Yes      | Tair password  |             |


## Tair 

For a hosted [Tair Cloud](https://www.alibabacloud.com/help/en/tair/latest/step-1-create-a-tair-instance) version, provide the Tair instance URL:

**Example:**

```bash
TAIR_HOST="https://YOUR-TAIR-INSTANCE-URL.rds.aliyuncs.com"
TAIR_PORT="YOUR-TAIR-INSTANCE-PORT"
TAIR_USERNAME="YOUR-TAIR-INSTANCE-USER-NAME"
TAIR_PASSWORD="YOUR-TAIR-INSTANCE-PASSWORD"
```

The other parameters are optional and can be changed if needed.

## Running Tair Integration Tests

A suite of integration tests verifies the Tair integration. Launch the test suite with this command:

```bash
python3 -m pytest tests/extensions_provier/test_tair_store.py
```
