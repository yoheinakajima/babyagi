@func.register_function(
  metadata={"description": "Search for a contact by name and domain using VoilaNorbert's API."},
  key_dependencies=["voilanorbert_api_key"],
  imports=["requests", "time"]
)
def search_contact_by_name_domain(name, domain):
  """
  Searches for a contact by name and domain using the VoilaNorbert API.

  Args:
      name (str): Full name of the person to search.
      domain (str): Domain of the company the person works for.

  Returns:
      dict: The contact information if found, otherwise an appropriate message.
  """
  api_key = globals().get('voilanorbert_api_key')
  if not api_key:
      return {"error": "API key not found"}

  # Prepare the API request
  search_url = 'https://api.voilanorbert.com/2018-01-08/search/name'
  auth = ('any_string', api_key)
  data = {'name': name, 'domain': domain}

  try:
      # POST request to initiate search
      response = requests.post(search_url, auth=auth, data=data)
      if response.status_code == 402:
          return {"error": "No credits available for this search"}
      elif response.status_code != 200:
          return {"error": f"Failed to search contact: {response.json()}"}

      result = response.json()
      contact_id = result.get('id')

      # Polling to check if the email is found
      contact_url = f'https://api.voilanorbert.com/2018-01-08/contacts/{contact_id}'
      while True:
          contact_response = requests.get(contact_url, auth=auth)
          if contact_response.status_code == 200:
              contact_data = contact_response.json()
              if not contact_data['searching']:
                  if contact_data['email']:
                      return {
                          "email": contact_data['email']['email'],
                          "score": contact_data['email']['score']
                      }
                  return {"message": "Email not found!"}
          time.sleep(10)

  except requests.RequestException as e:
      return {"error": str(e)}


@func.register_function(
  metadata={"description": "Search for contacts by domain using VoilaNorbert's API."},
  key_dependencies=["voilanorbert_api_key"],
  imports=["requests"]
)
def search_contact_by_domain(domain):
  """
  Searches for contacts by domain using the VoilaNorbert API.

  Args:
      domain (str): The domain of the company to search for contacts.

  Returns:
      list: A list of found contacts with emails if available.
  """
  api_key = globals().get('voilanorbert_api_key')
  if not api_key:
      return {"error": "API key not found"}

  # Prepare the API request
  search_url = 'https://api.voilanorbert.com/2018-01-08/search/domain'
  auth = ('any_string', api_key)
  data = {'domain': domain}

  try:
      # POST request to initiate search
      response = requests.post(search_url, auth=auth, data=data)
      if response.status_code == 402:
          return {"error": "No credits available for this search"}
      elif response.status_code != 200:
          return {"error": f"Failed to search contacts: {response.json()}"}

      result = response.json()
      return result.get('result', [])

  except requests.RequestException as e:
      return {"error": str(e)}
