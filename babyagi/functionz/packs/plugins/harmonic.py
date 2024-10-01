# Harmonic API Functions Pack for Functionz Framework


@func.register_function(
    metadata={"description": "Fetch a company's enrichment data using its identifier (URL or domain)."},
    key_dependencies=["harmonic_api_key"],
    imports=[{"name": "requests", "lib": "requests"}]
)
def harmonic_enrich_company(identifier):
    """
    Enrich a company using its URL, domain, or identifier.
    Returns the full response from Harmonic API.
    """
    api_key = globals()['harmonic_api_key']
    url = "https://api.harmonic.ai/companies"
    headers = {"accept": "application/json", "apikey": api_key}

    # Determine the appropriate parameter based on identifier type
    if identifier.startswith('http'):
        params = {"crunchbase_url": identifier} if 'crunchbase.com' in identifier else {"website_url": identifier}
    elif '.' in identifier and not identifier.startswith('http'):
        params = {"website_domain": identifier}
    else:
        url += f"/{identifier}"
        params = {}

    # Use POST if parameters are present, otherwise GET
    response = requests.post(url, headers=headers, params=params) if params else requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


@func.register_function(
    metadata={"description": "Search for companies using a set of keywords."},
    key_dependencies=["harmonic_api_key"],
    imports=[{"name": "requests", "lib": "requests"}]
)
def harmonic_search_companies(keywords, include_ids_only=False):
    """
    Search for companies using keywords.
    Returns a list of companies and their metadata.
    """
    api_key = globals()['harmonic_api_key']
    url = "https://api.harmonic.ai/search/companies_by_keywords"
    headers = {"accept": "application/json", "apikey": api_key, "Content-Type": "application/json"}

    data = {"keywords": keywords, "include_ids_only": include_ids_only}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


@func.register_function(
    metadata={"description": "Fetch detailed information about a person using their ID."},
    key_dependencies=["harmonic_api_key"],
    imports=[{"name": "requests", "lib": "requests"}]
)
def harmonic_enrich_person_by_id(person_id):
    """
    Retrieve detailed information about a person using their Harmonic ID.
    """
    api_key = globals()['harmonic_api_key']
    url = f"https://api.harmonic.ai/persons/{person_id}"
    headers = {"accept": "application/json", "apikey": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
