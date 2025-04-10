import typing as t

try:
    from metadata import DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata


def update_with_substitutions(
    config: dict[str, t.Any], book_metadata: dict[str, DocumentMetadata]
) -> dict[str, t.Any]:
    substitutions = get_substitutions_mapping(book_metadata)
    try:
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    except KeyError:
        if "sphinx" not in config:
            config["sphinx"] = {}
        if "config" not in config["sphinx"]:
            config["sphinx"]["config"] = {}
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    return config


def get_substitutions_mapping(
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
        assert len([subs.pk for subs in metadata.substitutions]) == len(
            set([subs.pk for subs in metadata.substitutions])
        )
        for dp in metadata.substitutions:

            # if dp.item_type == "ref":
            #     pass  # get file count from target?
            # else:
            #     pass  # otherwise

            print(
                {
                    "pk": dp.pk,
                    "was": dp.was,
                    "item_type": dp.item_type,
                    "file_count": dp.file_count,
                    "prefix": dp.prefix,
                    "new_item_num": dp.new_item_num,
                }
            )
            print("-" * 50)
            # interesting that for many substitutions there is no new_item_num

            substitutions[dp.pk] = dp.new_value()
            # if dp.new_item_num and not dp.file_count:
            #     substitutions[dp.pk] = f"{dp.prefix}{dp.new_item_num}"
            # elif dp.new_item_num:
            #     substitutions[dp.pk] = f"{dp.file_count}.{dp.prefix}{dp.new_item_num}"
            # else:
            #     substitutions[dp.pk] = dp.was

    return substitutions
