try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Footnote(MySQLModel, table=True):
    """
    This is imporant when splitting the file.

    Footnote reference outputed by docx2html:
    ```html
    <sup>
        <a href="#footnote-1" id="footnote-ref-1">[1]</a>
    </sup>
    ```
    Target added at the end of the file:
    ```html
    <ol>
        <li id="footnote-1">
            <p> Content <a href="#footnote-ref-1">↑</a></p>
        </li>
    </ol>
    ```
    """

    __tablename__ = "footnotes"

    html: str
    number: str
    target_id: str
    # referenced_in: str | None = None
