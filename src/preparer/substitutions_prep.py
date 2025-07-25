import bs4

try:
    from metadata import DocumentMetadata, SubstitutionDatapoint, TargetDatapoint
    from state import DocumentState
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, SubstitutionDatapoint, TargetDatapoint
    from .state import DocumentState


def count_targets_for_substitutions(
    soup: bs4.BeautifulSoup, metadata: DocumentMetadata, dstate: DocumentState
) -> bs4.BeautifulSoup:
    update_datapoints_for_targets(soup, metadata.substitutions)
    update_datapoints_for_targets(soup, metadata.targets)
    return soup


def update_datapoints_for_targets(
    soup: bs4.BeautifulSoup,
    # metadata: DocumentMetadata,
    datapoints: list[SubstitutionDatapoint | TargetDatapoint],
) -> bs4.BeautifulSoup:
    """
    This function is similar (but not identic) to
    "wordprocessor/numbering_refs/_update_datapoints_for_targets()".
    Especially note that we omit when dp.is_digital == False.
    """
    prev_item_num = {
        "heading": 0,
        "equation": 0,
        "figure": 0,
        "table": 0,
        "": 0,
    }
    ommited_count = {
        "heading": 0,
        "equation": 0,
        "figure": 0,
        "table": 0,
        "": 0,
    }
    for dp in datapoints:
        if dp.item_type == "ref":
            assert dp.prev_item_num is None  # TODO: temp, remove this if it works
        if dp.prev_item_num is None:  # assumes refs always have prev_item_num == None
            pass
        elif dp.is_digital == False:
            val = 0 if prev_item_num[dp.item_type] == dp.prev_item_num else 1
            ommited_count[dp.item_type] += val
        else:
            dp.new_item_num = dp.prev_item_num - ommited_count[dp.item_type]
        prev_item_num[dp.item_type] = dp.prev_item_num
    return soup
