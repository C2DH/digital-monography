import bs4


def replace_alt_texts(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    for img in soup.find_all("img", alt=True):
        img["alt"] = img["alt"].replace("\n", " ")
    return soup
