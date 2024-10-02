import bs4
import secrets
import string


def add_id_to_captions_without_bookmarks(
    html_soup: bs4.BeautifulSoup,
) -> bs4.BeautifulSoup:
    for caption in html_soup.find_all("p", {"class": "dgt-mon-caption"}):
        anchors = caption.find("a", id=True)
        if anchors is None:
            a = html_soup.new_tag("a")
            new_id = "".join(secrets.choice(string.digits) for i in range(9))
            a["id"] = "_Unref" + new_id
            caption.insert(0, a)
    return html_soup
