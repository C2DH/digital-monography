import typing as t

try:
    from metadata import (
        AssetRecord,
        CitationGroupDatapoint,
        CitationItemDatapoint,
        DocumentMetadata,
        RefDatapoint,
        TargetDatapoint,
    )
except (ImportError, ModuleNotFoundError):
    from .metadata import (
        AssetRecord,
        CitationGroupDatapoint,
        CitationItemDatapoint,
        DocumentMetadata,
        RefDatapoint,
        TargetDatapoint,
    )


def make_metadata_report(
    metadata: DocumentMetadata,
    filename: str,
) -> None:
    targets = ""
    citations = ""
    refs = ""
    for dp in metadata.targets:
        dp: TargetDatapoint
        targets += f"* {dp.elem}\n"
    if targets:
        targets = "## Reference targets\n\n" + targets + "\n\n"

    for dp in metadata.citation_groups:
        dp: CitationGroupDatapoint
        citations += f"* {dp.plainCitation}\n"
    if citations:
        citations = "## Citations\n\n" + citations + "\n\n"

    for dp in metadata.refs:
        dp: RefDatapoint
        refs += f"* {dp.elem}\n"
    if refs:
        refs = "## References\n\n" + refs + "\n\n"

    report = f"""\
# Metadata extracted from "{filename}"

{targets}
{citations}
{refs}

"""
    return report
