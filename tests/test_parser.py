from app.services.parser import parse_html


def test_parse_html_extracts_basic_page_data():
    html = """
    <html>
      <head>
        <title>Example Page</title>
        <meta name="description" content="Example description">
      </head>
      <body>
        <h1>Main heading</h1>
        <a href="/one">One</a>
        <a href="/two">Two</a>
      </body>
    </html>
    """

    result = parse_html(html)

    assert result["title"] == "Example Page"
    assert result["h1"] == "Main heading"
    assert result["meta_description"] == "Example description"
    assert result["links_count"] == 2


def test_parse_html_handles_missing_fields():
    result = parse_html("<html><body>No title here</body></html>")

    assert result["title"] is None
    assert result["h1"] is None
    assert result["meta_description"] is None
    assert result["links_count"] == 0
