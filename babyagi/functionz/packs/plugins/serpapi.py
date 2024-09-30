@func.register_function(
  metadata={
      "description": "Perform a search using the latest SerpApi Python client library with customizable parameters."
  },
  key_dependencies=["serpapi_api_key"],
  imports=["serpapi"]
)
def serpapi_search_v2(query: str, engine: str = "google", location: str = "United States", language: str = "en", country: str = "us", safe_search: bool = False, num_results: int = 10, start: int = 0, async_request: bool = False, output_format: str = "json"):
  """
  Perform a search using the SerpApi service with a flexible set of parameters.

  Args:
      query (str): The search query.
      engine (str): The search engine to use (e.g., 'google', 'bing'). Default is 'google'.
      location (str): The location to target the search. Default is 'United States'.
      language (str): UI language for the search. Default is 'en'.
      country (str): Country code for the search. Default is 'us'.
      safe_search (bool): Flag for SafeSearch filtering. Default is False.
      num_results (int): Number of search results to retrieve. Default is 10.
      start (int): Pagination offset. Default is 0.
      async_request (bool): Whether to make an asynchronous request. Default is False.
      output_format (str): Format of the output ('json' or 'html'). Default is 'json'.

  Returns:
      dict or str: The search results in the specified format.
  """
  # Import necessary modules and classes within function scope.

  # Get the API key from the global variables.
  api_key = globals().get("serpapi_api_key", "")
  if not api_key:
      raise ValueError("API key is missing. Please provide a valid SerpApi key.")

  # Initialize the SerpApi client.
  client = serpapi.Client(api_key=api_key)

  # Define the search parameters.
  params = {
      "q": query,
      "engine": engine,
      "location": location,
      "hl": language,
      "gl": country,
      "safe": "active" if safe_search else "off",
      "num": num_results,
      "start": start,
      "async": async_request,
      "output": output_format,
  }

  try:
      # Perform the search and get the results.
      search_results = client.search(**params)

      # Return the results in the specified format.
      if output_format == "json":
          return search_results.as_dict()
      elif output_format == "html":
          return search_results.get("raw_html", "No HTML content found.")
      else:
          raise ValueError("Invalid output format specified. Choose either 'json' or 'html'.")

  except requests.exceptions.HTTPError as e:
      # Handle potential SerpApi errors and HTTP errors.
      return {"error": str(e)}
