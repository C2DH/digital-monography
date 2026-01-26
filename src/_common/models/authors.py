import datetime
import sqlmodel

from ._base import MySQLModel


class LinkAuthorsBooks(sqlmodel.SQLModel, table=True):
    """
    Links authors to books in a many-to-many relationship
    (one author can write multiple books, one book can have multiple authors).
    """

    __tablename__ = "link_authors_books"

    author_id: int = sqlmodel.Field(foreign_key="authors.id", primary_key=True)
    book_id: int = sqlmodel.Field(foreign_key="books.id", primary_key=True)


class Author(MySQLModel, table=True):
    """
    Authors are extracted from a frontmatter or _myst.yml file.
    See https://mystmd.org/guide/frontmatter#frontmatter-authors
    """

    __tablename__ = "authors"

    id: int = sqlmodel.Field(primary_key=True)
    name: str = sqlmodel.Field()
    books: list["Book"] = sqlmodel.Relationship(
        back_populates="authors", link_model=LinkAuthorsBooks
    )


class Book(MySQLModel, table=True):
    __tablename__ = "books"

    id: int = sqlmodel.Field(primary_key=True)
    slug: str = sqlmodel.Field(index=True, nullable=False, unique=True)
    title: str = sqlmodel.Field()
    updated: datetime.datetime = sqlmodel.Field()
    authors: list[Author] = sqlmodel.Relationship(
        back_populates="books", link_model=LinkAuthorsBooks
    )
