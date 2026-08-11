from bs4 import BeautifulSoup

def main():
    zoning_root = "data/2026-50/zoning-law-law-no-2026-50.html"
    with open(zoning_root, 'r') as file:
        html = file.read()
    soup = BeautifulSoup(html, 'html.parser')

    all_sections = soup.find_all(class_="collapse-region")
    for section in all_sections:
        print("===================")

        section_title = section.find("h2").text
        print(section_title)
        url = section.find('a', href=True)['href']
        print(url)
        
        for subsection in section.find_all("li"):
            print()
            print(subsection.text)
            a = subsection.find("a", href=True)
            if a:
                print(a['href'])



if __name__ == "__main__":
    main()