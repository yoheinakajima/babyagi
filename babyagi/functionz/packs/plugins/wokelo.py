@func.register_function(
  metadata={"description": "Get an authentication token using the Wokelo API credentials."},
  key_dependencies=["wokelo_username", "wokelo_password"],
  imports=[{"name": "requests", "lib": "requests"}]
)
def get_auth_token():
  """Obtain an authentication token using Wokelo API credentials stored as secrets."""
  import requests
  BASE_URL = 'https://api.wokelo.ai'
  url = BASE_URL + '/auth/token'

  headers = {"Content-Type": "application/x-www-form-urlencoded"}
  data = {
      "client_id": "B5I07FeItrqH5V8ytQKNwHPDHeMQnGBheg7A6FAg",
      "client_secret": "JkVEP6FZhTkolz9vwkFSFAMVKLO0r9CnYU2RlGcRSzxZGZSkdSbSCed30VHg55IWU94F3sh0fTGUy8dTGslQZmcpCGvPhEUs9w3uobWa4ftXvsahriFCReRIxEUdd2f8",
      "grant_type": "password",
      "username": globals()['wokelo_username'],
      "password": globals()['wokelo_password'],
  }

  response = requests.post(url, headers=headers, data=data)

  if response.status_code == 200:
      # Successfully obtained token
      token_info = response.json()
      return token_info.get("access_token")
  else:
      return {"error": f"Failed to obtain token. Status code: {response.status_code}", "details": response.text}


@func.register_function(
  metadata={"description": "Create an industry snapshot report in Wokelo."},
  dependencies=["get_auth_token"],
  imports=[{"name": "requests", "lib": "requests"}]
)
def create_industry_snapshot(access_token: str, industry_name: str):
  """Initiate a new industry snapshot report."""
  import requests
  BASE_URL = 'https://api.wokelo.ai'
  url = f'{BASE_URL}/api/industry_primer/v3/start/'
  headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
  payload = {"industry": industry_name}

  response = requests.post(url, json=payload, headers=headers)
  if response.status_code == 200:
      return response.json().get('report_id')
  else:
      return {"error": "Failed to create industry snapshot.", "details": response.text}


@func.register_function(
  metadata={"description": "Check the status of an industry report using its report ID."},
  dependencies=["get_auth_token"],
  imports=[{"name": "requests", "lib": "requests"}]
)
def check_report_status(access_token: str, report_id: str):
  """Check the status of a generated report in Wokelo."""
  import requests
  BASE_URL = 'https://api.wokelo.ai'
  url = f'{BASE_URL}/api/assets/get_report_status/?report_id={report_id}'
  headers = {'Authorization': f'Bearer {access_token}'}

  response = requests.get(url, headers=headers)
  if response.status_code == 200:
      return response.json()
  else:
      return {"error": "Failed to check report status.", "details": response.text}


@func.register_function(
  metadata={"description": "Download the generated report from Wokelo."},
  dependencies=["get_auth_token"],
  imports=[{"name": "requests", "lib": "requests"}]
)
def download_report(access_token: str, report_id: str, file_type: str = 'pdf'):
  """Download a specific report in a given file format."""
  import requests
  BASE_URL = 'https://api.wokelo.ai'
  url = f'{BASE_URL}/api/assets/download_report/'
  headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
  payload = {"file_type": file_type, "report_id": report_id}

  response = requests.post(url, json=payload, headers=headers)
  if response.status_code == 200:
      return response.content
  else:
      return {"error": "Failed to download report.", "details": response.text}


@func.register_function(
  metadata={"description": "Generate an industry report in Wokelo by tying all steps together."},
  dependencies=["get_auth_token", "create_industry_snapshot", "check_report_status", "download_report"],
  imports=[{"name": "time", "lib": "time"}]
)
def generate_industry_report(industry_name: str, file_type: str = 'pdf'):
  """
  Complete workflow for generating and downloading an industry report.

  Args:
      industry_name (str): The name of the industry to generate the report for.
      file_type (str): The format of the report file to be downloaded. Default is 'pdf'.

  Returns:
      str: File path of the downloaded report.
  """
  # Step 1: Get an authentication token.
  access_token = get_auth_token()
  if not isinstance(access_token, str):
      return access_token  # If there's an error, return the error message.

  # Step 2: Create an industry snapshot.
  report_id = create_industry_snapshot(access_token, industry_name)
  if not isinstance(report_id, str):
      return report_id  # If there's an error, return the error message.

  # Step 3: Check report status until it's ready.
  print(f"Initiated report creation. Waiting for the report (ID: {report_id}) to be exported.")
  while True:
      status_info = check_report_status(access_token, report_id)
      if 'status' in status_info and status_info['status'] == 'exported':
          print(f"Report is ready for download: {report_id}")
          break
      elif 'status' in status_info:
          print(f"Current report status: {status_info['status']}. Checking again in 30 seconds...")
      else:
          return status_info  # Error occurred.
      time.sleep(30)

  # Step 4: Download the report.
  report_content = download_report(access_token, report_id, file_type)
  if isinstance(report_content, dict) and 'error' in report_content:
      return report_content  # Return the error if download failed.

  # Step 5: Save the report locally.
  report_filename = f'report_{report_id}.{file_type}'
  with open(report_filename, 'wb') as report_file:
      report_file.write(report_content)

  return f"Report downloaded successfully: {report_filename}"
