import sqlmodel
import uuid

try:
    from ._base import MySQLModel
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore


class Ref(MySQLModel, table=True):
    """
    Reference (link or cross-reference) to a Target (bookmark, heading or caption)
    extracted from a docx document.
    """

    __tablename__ = "refs"

    # pk: str = sqlmodel.Field(primary_key=True, default=str(uuid.uuid4()))
    # pk: uuid.UUID = sqlmodel.Field(primary_key=True, default=uuid.uuid4())
    fn: str
    target_id: str
    text: str
    href: str
    prev_string: str
    prev_href: str
    elem: str
    asset_id: str | None = sqlmodel.Field(default=None)


# class RefDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     fn: str
#     target_id: str
#     text: str
#     href: str
#     prev_string: str
#     prev_href: str
#     elem: str
#     asset_id: str | None = None

#     @staticmethod
#     def get_s3_key(slug: str, stem: str) -> str:
#         return f"{slug}/{stem}.json"

#     def is_external(self) -> bool:
#         """Is it a link to an external target
#         (currently only email and http protocol is recognized)."""
#         if self.href.startswith("mailto:") and "@" in self.href:
#             return True
#         return self.href.startswith("http") and ".sharepoint.com/" not in self.href

#     def is_internal_infile(self) -> bool:
#         "Is it a link to a target in the same document (file)?"
#         return self.href.startswith("#")

#     def is_internal_f2f(self) -> bool:
#         "Is it a link to another document (file)?"
#         if self.is_internal_infile() or self.is_external():
#             return False
#         return "#" in self.href
