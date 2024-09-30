# 1. Crawl a website and initiate a crawl job.
@func.register_function(
    metadata={"description": "Submits a crawl job for a website and returns a job ID."},
    key_dependencies=["firecrawl_api_key"],
    imports={"name":"firecrawl","lib":"firecrawl-py"}
)
def crawl_website(url: str, limit: int = 100, formats: list = ["markdown", "html"], poll_interval: int = 30):
    """
    Submits a crawl job for the given URL and returns the crawl job status and job ID.
    """
    from firecrawl import FirecrawlApp
    api_key = globals()['firecrawl_api_key']
    app = FirecrawlApp(api_key=api_key)

    try:
        crawl_status = app.crawl_url(
            url, 
            params={'limit': limit, 'scrapeOptions': {'formats': formats}},
            poll_interval=poll_interval
        )
        return crawl_status
    except Exception as e:
        return {"error": str(e)}


# 2. Check the status of a crawl job.
@func.register_function(
    metadata={"description": "Checks the status of an ongoing or completed crawl job by its job ID."},
    key_dependencies=["firecrawl_api_key"],
    imports={"name":"firecrawl","lib":"firecrawl-py"}
)
def check_crawl_status(crawl_id: str):
    """
    Checks the status of the crawl job and returns the job details including markdown and HTML data.
    """
    from firecrawl import FirecrawlApp
    api_key = globals()['firecrawl_api_key']
    app = FirecrawlApp(api_key=api_key)

    try:
        crawl_status = app.check_crawl_status(crawl_id)
        return crawl_status
    except Exception as e:
        return {"error": str(e)}


# 3. Scrape a single website URL for markdown and HTML data.
@func.register_function(
    metadata={"description": "Scrapes a single URL and returns markdown and HTML content."},
    key_dependencies=["firecrawl_api_key"],
    imports={"name":"firecrawl","lib":"firecrawl-py"}
)
def scrape_website(url: str, formats: list = ["markdown", "html"]):
    """
    Scrapes the given URL and returns the data (markdown, HTML, and metadata).
    """
    from firecrawl import FirecrawlApp
    api_key = globals()['firecrawl_api_key']
    app = FirecrawlApp(api_key=api_key)

    try:
        scrape_result = app.scrape_url(url, params={'formats': formats})
        return scrape_result
    except Exception as e:
        return {"error": str(e)}
