import pathlib
import typing as t

try:
    from metadata import DocumentMetadata, FileDatapoint, TargetDatapoint
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, FileDatapoint, TargetDatapoint


def update_with_substitutions(
    config: dict[str, t.Any], book_metadata: dict[str, DocumentMetadata]
) -> dict[str, t.Any]:
    _update_file_count(config, book_metadata)
    update_substitutions_in_refs(book_metadata)
    substitutions = get_substitutions_mapping(book_metadata)
    """
    Updating "myst_substitutions" in the config file is only for redundancy.
    The replacement is done in builder/main.py before JupyterBook is being run.
    """
    try:
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    except KeyError:
        if "sphinx" not in config:
            config["sphinx"] = {}
        if "config" not in config["sphinx"]:
            config["sphinx"]["config"] = {}
        config["sphinx"]["config"]["myst_substitutions"] = substitutions
    return config


def _update_file_count(
    config: dict[str : t.Any], book_metadata: dict[str, DocumentMetadata]
) -> None:
    if "dgtmon" not in config or "prefixes" not in config["dgtmon"]:
        return
    prefixes = config["dgtmon"]["prefixes"]
    if type(prefixes) == list and type(prefixes[0]) == dict:
        prefixes = {k: v for kv in prefixes for k, v in kv.items()}
    if type(prefixes) != dict or len(prefixes) == 0:
        return
    ###
    for metadata in book_metadata.values():
        for stem, prefix in prefixes.items():
            metadata.add_file(FileDatapoint(stem=stem, prefix=str(prefix)))


def update_substitutions_in_refs(book_metadata: dict[str, DocumentMetadata]) -> None:
    """
    Update values of substitutions in the references based on targets
    found in all manuscript files. This updating is important for both
    updating the config file and for replacing the placeholders in the
    buiders/main.py procedure.
    """
    for metadata in book_metadata.values():
        for dp in metadata.substitutions:
            if dp.item_type == "ref":
                if dp.target_fn:
                    fn = pathlib.Path(dp.target_fn).stem
                    # fn = dp.target_fn.stem
                    if fn not in book_metadata:
                        continue
                    target_metadata = book_metadata[fn]
                else:
                    target_metadata = metadata
                target: TargetDatapoint = target_metadata.get_target(dp.placeholder)
                if target:
                    dp.file_count = target.file_count
                    dp.prefix = target.prefix
                    dp.new_item_num = target.new_item_num


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

    For the digital version, the replacement is supposed to be made by JupyterBook
    (in reality, the replacement is done in builder/main.py and JupyterBook
    substitution configured via "myst_substitutions" is only for redundancy).
    For the paper version, the replacement should be done automatically in MS Word,
    without the need of this mapping.
    """
    substitutions = {}
    for metadata in book_metadata.values():
        assert len([subs.pk for subs in metadata.substitutions]) == len(
            set([subs.pk for subs in metadata.substitutions])
        )
        file_prefix = None
        for file in metadata.files:
            if file.stem == metadata.filepath.stem:
                file_prefix = str(file.prefix)
        for dp in metadata.substitutions:
            substitutions[dp.pk] = dp.new_value(file_prefix)
    return substitutions
