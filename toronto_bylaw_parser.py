from bs4 import Tag


def extract_table_of_contents(soup):
    toc_data = []
    for tr in soup.find_all("tr"):
        links = tr.find("a", href=True)
        if links:
            cell_values = tr.find_all("td")
            section = cell_values[0].get_text(strip=True, separator=" ")
            if "chapter" in section.lower():
                toc_data.append(
                    {
                        "section": section,
                        "title": cell_values[2].get_text(strip=True, separator=" "),
                        "link": links["href"],
                    }
                )
    return toc_data


def extract_content_rows(soup):
    current_chapter = None
    current_section = None
    rows = []
    item_counter = 0

    for el in soup.descendants:
        if not isinstance(el, Tag):
            continue

        if el.name == "h1":
            current_chapter = el.get_text(strip=True)
            current_chapter = current_chapter.replace("Chapter ", "")
        elif el.name == "h2":
            current_section = el.get_text(strip=True)
        elif el.name == "tr":
            # skip wrapper tds that just contain another table —
            # only capture leaf content cells to avoid duplicate/parent text
            if el.find("table") is not None:
                continue
            text = el.get_text(separator=" ", strip=True)
            if text:
                rows.append(
                    {
                        "chunk_id": item_counter,
                        "chapter": current_chapter,
                        "section": current_section,
                        "text": text,
                    }
                )
                item_counter += 1

    return rows
