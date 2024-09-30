import nbformat


def tags_to_myst_crossref_targets(nb: nbformat.NotebookNode) -> None:
    for cell in nb.cells:
        for tag in cell["metadata"].get("tags", []):
            if tag.split("-")[0].lower() in [
                "h",
                "heading",
                "header",
                "fig",
                "figure",
                "table",
                "tbl",
            ]:
                if type(cell["source"]) == str:
                    cell["source"] = f"({tag})=\n" + cell["source"]
                elif type(cell["source"]) == list:
                    cell["source"].insert(0, f"({tag})=\n")
