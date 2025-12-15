import bs4
import json

from src._common.constants import CLS_STATE_TABLE_JSONDATA
from src._common.state import DocumentState


def hide_metadata_in_html(
    html_soup: bs4.BeautifulSoup, docstate: DocumentState
) -> bs4.BeautifulSoup:
    """
    Hide all state records in a hidden <script> tag at the end of a html file.
    """
    json_elem = html_soup.new_tag("script")
    json_elem["type"] = "application/json"
    json_elem["class"] = CLS_STATE_TABLE_JSONDATA
    json_elem["hidden"] = "hidden"
    json_elem.string = json.dumps(docstate.to_dict())
    html_soup.append(json_elem)
    return html_soup
