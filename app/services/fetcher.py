import httpx

from app.config import get_fetch_timeout_seconds, get_user_agent


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=get_fetch_timeout_seconds(),
        follow_redirects=True,
        headers={"User-Agent": get_user_agent()},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
