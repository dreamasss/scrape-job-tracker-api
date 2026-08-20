import httpx


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": "ScrapeJobTrackerBot/0.1"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
