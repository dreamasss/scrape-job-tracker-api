from bs4 import BeautifulSoup


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def parse_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = clean_text(soup.title.string if soup.title and soup.title.string else None)

    h1_tag = soup.find("h1")
    h1 = clean_text(h1_tag.get_text(" ", strip=True) if h1_tag else None)

    description_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = clean_text(
        description_tag.get("content") if description_tag else None
    )

    links_count = len(soup.find_all("a"))

    return {
        "title": title,
        "h1": h1,
        "meta_description": meta_description,
        "links_count": links_count,
    }
