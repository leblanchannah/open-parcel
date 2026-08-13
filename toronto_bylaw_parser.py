import os

import requests
from bs4 import BeautifulSoup, Tag

root_page = "https://www.toronto.ca/zoning/bylaw_amendments/ZBL_NewProvision_Chapter1.htm"
cache_path = "data/toronto/ZBL_NewProvision_Chapter1.htm"

if os.path.exists(cache_path):
    print("file exists")
    with open(cache_path, encoding="utf-8") as file:
        html = file.read()
else:
    print("fetching file")
    response = requests.get(root_page)
    html = response.text
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as file:
        file.write(html)

soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

toc_index = next((i for i, x in enumerate(tables) if "Table of Contents" in x.text), None)

if toc_index is not None:
    toc = tables[toc_index]
    # left column - table of contents
    toc_data = []
    for tr in toc.find_all("tr")[1:]:
        links = tr.find("a", href=True)
        if links:
            cell_values = tr.find_all("td")
            toc_data.append(
                {
                    "section": cell_values[0].text,
                    "title": cell_values[2].text,
                    "link": links["href"],
                }
            )
else:
    print("No Table of Contents found")


# right table - content
content_header = soup.find("h1")

content_data = []
if content_header is not None and content_header.parent is not None:
    content = content_header.parent
    section = None
    for item in content:
        if isinstance(item, Tag) and item.name == "h2":
            section = item.get_text(strip=True)
            content_data.append(
                {
                    "section": section,
                    "text": item.get_text(strip=True),
                }
            )


# print(pd.DataFrame(content_data))


# version date
# https://open.toronto.ca/dataset/zoning-by-law/
