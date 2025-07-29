import bs4
import json

try:
    from metadata import DocumentMetadata
    from constants import CLS_METADATA_TABLE_JSONDATA, CLS_STATE_TABLE_JSONDATA
    from state import DocumentState
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata
    from .constants import CLS_METADATA_TABLE_JSONDATA, CLS_STATE_TABLE_JSONDATA
    from .state import DocumentState


def hide_metadata_in_html(
    html_soup: bs4.BeautifulSoup, metadata: DocumentMetadata, dstate: DocumentState
) -> bs4.BeautifulSoup:
    """
    Hide all metadata records and state records in a hidden <script> tag at the end of
    a html file.
    """
    # metadata
    json_elem = html_soup.new_tag("script")
    json_elem["type"] = "application/json"
    json_elem["class"] = CLS_METADATA_TABLE_JSONDATA
    json_elem["hidden"] = "hidden"
    json_elem.string = json.dumps(metadata.to_json())
    html_soup.append(json_elem)
    # document state
    json_elem = html_soup.new_tag("script")
    json_elem["type"] = "application/json"
    json_elem["class"] = CLS_STATE_TABLE_JSONDATA
    json_elem["hidden"] = "hidden"
    json_elem.string = json.dumps(dstate.to_dict())
    html_soup.append(json_elem)
    return html_soup
