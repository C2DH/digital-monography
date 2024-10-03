import bs4
import copy
import secrets
import string


def add_id_to_captions_without_bookmarks(
    html_soup: bs4.BeautifulSoup,
) -> bs4.BeautifulSoup:
    for caption in html_soup.find_all("p", {"class": "dgt-mon-caption"}):
        print("-" * 25)
        a = caption.find("a", id=True)
        if a is None:
            a = html_soup.new_tag("a")
            new_id = "".join(secrets.choice(string.digits) for i in range(9))
            a["id"] = "_Unref" + new_id
        else:
            a = a.extract()

        # TODO:
        # Here is a good place to replace static numbering with dynamic template

        contents = copy.copy(caption.contents)
        for el in contents:
            a.append(el)
        caption.contents = []
        caption.insert(0, a)
    return html_soup
