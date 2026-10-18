@func.register_function(
    metadata={
        "description": "Search the web with Parallel for current information and source URLs. No search API key is required."
    }
)
def parallel_search(objective: str, search_queries: list, search_context: dict = None) -> dict:
    """Search using one focused objective and related keyword queries."""
    from babyagi.functionz.core.parallel_search import call_parallel

    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("objective must be a nonempty string.")
    if (not isinstance(search_queries, list) or not search_queries
            or any(not isinstance(query, str) or not query.strip() for query in search_queries)):
        raise ValueError("search_queries must be a nonempty list of strings.")
    return call_parallel("web_search", {
        "objective": objective, "search_queries": search_queries,
    }, search_context=search_context)


@func.register_function(
    metadata={
        "description": "Fetch relevant page excerpts from HTTP or HTTPS URLs with Parallel. No search API key is required."
    }
)
def parallel_fetch(urls: list, objective: str = "", search_context: dict = None) -> dict:
    """Fetch up to 20 URLs; optionally focus excerpts with a short objective."""
    from urllib.parse import urlsplit
    from babyagi.functionz.core.parallel_search import call_parallel

    if not isinstance(urls, list) or not 1 <= len(urls) <= 20:
        raise ValueError("urls must contain between 1 and 20 HTTP or HTTPS URLs.")
    for url in urls:
        if not isinstance(url, str):
            raise ValueError("Each URL must be a string.")
        parsed = urlsplit(url)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None):
            raise ValueError("Each URL must be HTTP or HTTPS without embedded credentials.")
    if not isinstance(objective, str) or len(objective) > 200:
        raise ValueError("objective must be a string of at most 200 characters.")
    arguments = {"urls": urls}
    if objective:
        arguments["objective"] = objective
    return call_parallel("web_fetch", arguments, search_context=search_context)
