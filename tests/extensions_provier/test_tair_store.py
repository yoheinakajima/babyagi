import pytest
import os
"""
os.environ["TAIR_HOST"] = "localhost"
os.environ["TAIR_PORT"] = "6379"
os.environ["TAIR_USERNAME"] = "{username}"
os.environ["TAIR_PASSWORD"] = "{passwd}"
"""
from extensions.tair_storage import can_import, TairResultsStorage

TASK_COUNT = 10
TOP_K = 5
OPENAI_API_KEY = None
LLM_MODEL = "gpt-3.5-turbo"
LLAMA_MODEL_PATH = None
RESULTS_STORE_NAME = "babyagi_index"
OBJECTIVE = None


class TaskResult:
    def __init__(self, task, result, result_id):
        self.task = task
        self.result = result
        self.result_id = result_id


@pytest.fixture
def tair_storage():
    TAIR_HOST = os.getenv("TAIR_HOST", "")
    if TAIR_HOST and can_import("extensions.tair_storage"):
        TAIR_PORT = int(os.getenv("TAIR_PORT", ""))
        TAIR_USERNAME = os.getenv("TAIR_USERNAME", "")
        TAIR_PASSWORD = os.getenv("TAIR_PASSWORD", "")
        print("\nUsing results storage: " + "\033[93m\033[1m" + "Tair" + "\033[0m\033[0m")
        return TairResultsStorage(OPENAI_API_KEY, TAIR_HOST, TAIR_PORT, TAIR_USERNAME, TAIR_PASSWORD,
                                  LLM_MODEL, LLAMA_MODEL_PATH, RESULTS_STORE_NAME, OBJECTIVE, mock_embedding=True)
    return None


def test_tair_upsert_query(tair_storage):
    if tair_storage == None:
        print("\nPlease Config environment for: " + "\033[93m\033[1m" + "Tair" + "\033[0m\033[0m")
        return

    tasks = [TaskResult({"task_name": f"search {i}", "task_id": "weather"}, f"Sunshine {i}", i) for i in
             range(TASK_COUNT)]
    for task in tasks:
        tair_storage.add(task.task, task.result, task.result_id)
        assert tair_storage.key_exist(task.result_id)

    query_results = tair_storage.query(query=tasks[0].result, top_results_num=TOP_K)
    assert TOP_K == len(query_results)
    for i in range(TOP_K):
        if i == 0:
            assert f"search {i}" == query_results[i]

    tair_storage.delete_index()
