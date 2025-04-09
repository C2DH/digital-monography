import typing as t

try:
    from metadata import DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata


def update_with_substitutions(
    config: dict[str, t.Any], book_metadata: dict[str, DocumentMetadata]
) -> dict[str, t.Any]:
    substitutions = _get_substitutions_mapping(book_metadata)
    try:
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    except KeyError:
        if "sphinx" not in config:
            config["sphinx"] = {}
        if "config" not in config["sphinx"]:
            config["sphinx"]["config"] = {}
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    return config


def _get_substitutions_mapping(
    book_metadata: dict[str, DocumentMetadata],
) -> dict[str, str]:
    """
    Returns mapping of substitutions placeholders (SubstitutionDatapoint.pk) to the new values.
    This mapping is supposed to be written to JupyterBook config file:
    ```
    sphinx:
      config:
        myst_substitutions:
          substitution_pk: 'new_value'
    ```

    For the digital version, the replacement is supposed to be made by JupyterBook.
    For the paper version, the replacement should be done automatically in MS Word,
    without the need of this mapping.
    """
    substitutions = {}
    for metadata in book_metadata.values():
        for dp in metadata.substitutions:
            if dp.new_item_num and not dp.file_count:
                substitutions[dp.pk] = f"{dp.prefix}{dp.new_item_num}"
            elif dp.new_item_num:
                substitutions[dp.pk] = f"{dp.file_count}.{dp.prefix}{dp.new_item_num}"
            else:
                substitutions[dp.pk] = dp.was
    return substitutions
