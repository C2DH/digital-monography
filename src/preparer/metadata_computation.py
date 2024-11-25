import bs4

try:
    from metadata import AssetDatapoint, DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .metadata import AssetDatapoint, DocumentMetadata


def compute_additional_metadata_fields(metadata: DocumentMetadata) -> None:
    for asset in metadata.assets:
        asset: AssetDatapoint

        if asset.kwargs.get("digitalsource") is not None:
            digitalsource = metadata.filepath.parent / asset.kwargs.get("digitalsource")
            if digitalsource.exists():
                digital_stats = digitalsource.stat()
                digital_name = digitalsource.name
                digital_type = digitalsource.suffix
                digital_size = digital_stats.st_size  # in bytes
                digital_mtime = (
                    digital_stats.st_mtime
                )  # time of most recent content modification in seconds
                asset.kwargs.update(
                    {
                        "digitalname": digital_name,
                        "digitaltype": digital_type,
                        "digitalsize": digital_size,
                        "digitalmtime": digital_mtime,
                    }
                )

        if asset.kwargs.get("papersource") is not None:
            papersource = metadata.filepath.parent / asset.kwargs.get("papersource")
            if papersource.exists():
                paper_stats = papersource.stat()
                paper_name = papersource.name
                paper_type = papersource.suffix
                paper_size = paper_stats.st_size  # in bytes
                paper_mtime = (
                    paper_stats.st_mtime
                )  # time of most recent content modification in seconds
                asset.kwargs.update(
                    {
                        "papername": paper_name,
                        "papertype": paper_type,
                        "papersize": paper_size,
                        "papermtime": paper_mtime,
                    }
                )
        caption = asset.kwargs.get("caption")
        caption: bs4.element.PageElement
        asset.kwargs["caption"] = caption.text

        asset.kwargs["location"] = metadata.filepath

        # in case of a conflict, alt text in a Metadata Table wins over embedded alt text
        if asset.kwargs.get("alttext") is None:
            elem = asset.kwargs.get("elem")
            elem_with_alttext = elem.find(alt=True)
            asset.kwargs["alttext"] = elem_with_alttext.get("alt")

    return metadata


"""
| x | file_name | | 
| x | file_type | | 
| x | file_size | | 
| x | last_mod | | 
| x | caption | | 
| x | alttext | | 
|   | file asset is included in | | 
|   | bookmark | but how? | 
|   | url to digital book | how? | 
|   | url to OneDrive | how? | 
|   | downloadable link to s3 | how? | 
|   | references | here? Maybe at next step when all refs and targets are created? | 
|   | comments | how? | 
"""
