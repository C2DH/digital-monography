import bs4

try:
    from metadata import DocumentMetadata, SubstitutionDatapoint, TargetDatapoint
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, SubstitutionDatapoint, TargetDatapoint


def count_targets_for_substitutions(
    soup: bs4.BeautifulSoup, metadata: DocumentMetadata
) -> bs4.BeautifulSoup:
    update_datapoints_for_targets(soup, metadata.substitutions)
    update_datapoints_for_targets(soup, metadata.targets)
    update_substitutions_for_refs(soup, metadata)
    return soup


def update_datapoints_for_targets(
    soup: bs4.BeautifulSoup,
    # metadata: DocumentMetadata,
    datapoints: list[SubstitutionDatapoint, TargetDatapoint],
) -> bs4.BeautifulSoup:
    # NOTE: maybe instead of targets, we should use substitutions
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


def update_substitutions_for_refs(
    soup: bs4.BeautifulSoup, metadata: DocumentMetadata
) -> bs4.BeautifulSoup:
    for subs in metadata.substitutions:
        if subs.item_type == "ref":
            target = metadata.get_target(subs.placeholder)
            if target is not None:
                # subs.file_count = target.file_count # I should not be needed it, right?
                subs.prefix = target.prefix
                subs.new_item_num = target.new_item_num

    return soup
