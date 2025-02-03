# import bs4
try:
    from constants import DEFAULT_SFS_DIR, FIELD_DIGITAL_SOURCE, FIELD_PAPER_SOURCE
    from metadata import AssetDatapoint, DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .constants import DEFAULT_SFS_DIR, FIELD_DIGITAL_SOURCE, FIELD_PAPER_SOURCE
    from .metadata import AssetDatapoint, DocumentMetadata


def compute_additional_metadata_fields(metadata: DocumentMetadata) -> None:
    root = pathlib.Path(DEFAULT_SFS_DIR) / metadata.filepath.parent
    for asset in metadata.assets:
        asset: AssetDatapoint

        if asset.kwargs.get(FIELD_DIGITAL_SOURCE) is not None:
            digitalsource = root / asset.kwargs.get(
                FIELD_DIGITAL_SOURCE
            )
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
                        "digitalexists": True,
                    }
                )
            else:
                asset.kwargs.update(
                    {
                        "digitalexists": False,
                    }
                )

        if asset.kwargs.get(FIELD_PAPER_SOURCE) is not None:
            papersource = metadata.filepath.parent / asset.kwargs.get(
                FIELD_PAPER_SOURCE
            )
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
                        "paperexists": True,
                    }
                )
            else:
                asset.kwargs.update(
                    {
                        "paperexists": False,
                    }
                )

        asset.kwargs["location"] = metadata.filepath

        elem = asset.kwargs.get("elem")

        # in case of a conflict, alt text in a Metadata Table wins over embedded alt text
        if asset.kwargs.get("alttext") is None:
            elem_with_alttext = elem.find(alt=True)
            if elem_with_alttext is not None:
                asset.kwargs["alttext"] = elem_with_alttext.get("alt")

        if elem is not None:
            asset.kwargs["elem"] = str(elem)

    return metadata


"""
| x | file_name | | 
| x | file_type | | 
| x | file_size | | 
| x | last_mod | | 
| x | caption | | 
| x | alttext | | 
| x | file asset is included in | | 
|   | bookmark | how? | 
|   | url to digital book | how? | 
|   | url to OneDrive | how? | 
|   | downloadable link to s3 | how? | 
|   | references | here? Maybe at next step when all refs and targets are created? | 
|   | comments | how? | 
"""
