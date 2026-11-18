"""Enrichment links from fixed templates. The model never writes URLs, so none can be invented."""
from urllib.parse import quote_plus

TEMPLATES = {
    "Khan Academy (videos, practice)": "https://www.khanacademy.org/search?page_search_query={q}",
    "Wolfram|Alpha (check a calculation)": "https://www.wolframalpha.com/input?i={q}",
    "GeoGebra (interactive models)": "https://www.geogebra.org/search/{q}",
    "Wikipedia (background)": "https://en.wikipedia.org/w/index.php?search={q}",
}


def links(title):
    return [{"name": name, "url": url.format(q=quote_plus(title))} for name, url in TEMPLATES.items()]
