from babyagi.functionz.core.framework import func

# Store API keys (both test and real) from Replit secrets into the function database
@func.register_function(
    metadata={"description": "Store PayMan API keys (test and real) from Replit secrets into the function database"},
    imports=["os"]
)
def store_payman_api_keys():
    # Store test API key
    func.add_key('payman_test_api_key', os.environ['PAYMAN_TEST_API_KEY'])
    # Store real API key
    func.add_key('payman_api_key', os.environ['PAYMAN_API_KEY'])


# Create Task Function
@func.register_function(
    metadata={"description": "Create a task on PayMan platform (test by default, real if 'real_money' is True)"},
    key_dependencies=["payman_test_api_key", "payman_api_key"],
    imports=["requests"]
)
def create_task(title: str, description: str, payout: int, currency: str = "USD", category: str = "MARKETING", real_money: bool = False):
    if real_money:
        api_key = globals()['payman_api_key']
        base_url = "https://agent.payman.ai/api"
    else:
        api_key = globals()['payman_test_api_key']
        base_url = "https://agent-sandbox.payman.ai/api"

    headers = {
        "x-payman-api-secret": api_key,
        "Content-Type": "application/json",
        "Accept": "application/vnd.payman.v1+json"
    }
    payload = {
        "title": title,
        "description": description,
        "payout": payout,  # Payout in cents (e.g. 5000 for $50)
        "currency": currency,
        "category": category,
        "requiredSubmissions": 1,
        "submissionPolicy": "OPEN_SUBMISSIONS_ONE_PER_USER"
    }
    try:
        response = requests.post(f"{base_url}/tasks", headers=headers, json=payload)
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}


# Get Task by ID Function
@func.register_function(
    metadata={"description": "Get a task by its ID on PayMan platform (test by default, real if 'real_money' is True)"},
    key_dependencies=["payman_test_api_key", "payman_api_key"],
    imports=["requests"]
)
def get_task_by_id(task_id: str, real_money: bool = False):
    if real_money:
        api_key = globals()['payman_api_key']
        base_url = "https://agent.payman.ai/api"
    else:
        api_key = globals()['payman_test_api_key']
        base_url = "https://agent-sandbox.payman.ai/api"

    headers = {
        "x-payman-api-secret": api_key,
        "Content-Type": "application/json",
        "Accept": "application/vnd.payman.v1+json"
    }
    try:
        response = requests.get(f"{base_url}/tasks/{task_id}", headers=headers)
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}


# Get All Tasks Function
@func.register_function(
    metadata={"description": "Get all tasks for the current organization on PayMan platform (test by default, real if 'real_money' is True)"},
    key_dependencies=["payman_test_api_key", "payman_api_key"],
    imports=["requests"]
)
def get_all_tasks(page: int = 0, limit: int = 20, real_money: bool = False):
    if real_money:
        api_key = globals()['payman_api_key']
        base_url = "https://agent.payman.ai/api"
    else:
        api_key = globals()['payman_test_api_key']
        base_url = "https://agent-sandbox.payman.ai/api"

    headers = {
        "x-payman-api-secret": api_key,
        "Content-Type": "application/json",
        "Accept": "application/vnd.payman.v1+json"
    }
    params = {
        "page": page,
        "limit": limit
    }
    try:
        response = requests.get(f"{base_url}/tasks", headers=headers, params=params)
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}


@func.register_function(
    metadata={"description": "Get all submissions for a task on PayMan platform (test by default, real if 'real_money' is True)"},
    key_dependencies=["payman_test_api_key", "payman_api_key"],
    imports=["requests"]
)
def get_task_submissions(task_id: str, statuses: list = None, page: int = 0, limit: int = 20, real_money: bool = False):
    if real_money:
        api_key = globals()['payman_api_key']
        base_url = "https://agent.payman.ai/api"
    else:
        api_key = globals()['payman_test_api_key']
        base_url = "https://agent-sandbox.payman.ai/api"

    headers = {
        "x-payman-api-secret": api_key,
        "Content-Type": "application/json",
        "Accept": "application/vnd.payman.v1+json"
    }

    params = {
        "page": page,
        "limit": limit
    }

    if statuses:
        params["statuses"] = ",".join(statuses)

    try:
        response = requests.get(f"{base_url}/tasks/{task_id}/submissions", headers=headers, params=params)
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}

# Approve Task Submission Function
@func.register_function(
    metadata={"description": "Approve a task submission on PayMan platform (test by default, real if 'real_money' is True)"},
    key_dependencies=["payman_test_api_key", "payman_api_key"],
    imports=["requests"]
)
def approve_task_submission(submission_id: str, real_money: bool = False):
    if real_money:
        api_key = globals()['payman_api_key']
        base_url = "https://agent.payman.ai/api"
    else:
        api_key = globals()['payman_test_api_key']
        base_url = "https://agent-sandbox.payman.ai/api"

    headers = {
        "x-payman-api-secret": api_key,
        "Content-Type": "application/json",
        "Accept": "application/vnd.payman.v1+json"
    }
    try:
        response = requests.post(f"{base_url}/tasks/submissions/{submission_id}/approve", headers=headers)
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}


# Reject Task Submission Function
@func.register_function(
    metadata={"description": "Reject a task submission on PayMan platform (test by default, real if 'real_money' is True)"},
    key_dependencies=["payman_test_api_key", "payman_api_key"],
    imports=["requests"]
)
def reject_task_submission(submission_id: str, rejection_reason: str, real_money: bool = False):
    if real_money:
        api_key = globals()['payman_api_key']
        base_url = "https://agent.payman.ai/api"
    else:
        api_key = globals()['payman_test_api_key']
        base_url = "https://agent-sandbox.payman.ai/api"

    headers = {
        "x-payman-api-secret": api_key,
        "Content-Type": "application/json",
        "Accept": "application/vnd.payman.v1+json"
    }
    try:
        response = requests.post(f"{base_url}/tasks/submissions/{submission_id}/reject", headers=headers, json=rejection_reason)
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e)}
