import logging
import sqlmodel

from src._common.models import *


def select_by_slug(
    session: sqlmodel.Session,
    model: Asset | CitationGroup | CitationItem | Heading,
    slug: str,
) -> list[dict[str, str | int | bool]]:
    """
    Query the database for a model by its slug and dump to a json serializable format.
    """
    assert isinstance(model, sqlmodel.main.SQLModelMetaclass)
    if not hasattr(model, "slug"):
        logging.error(f"Model {model.__name__} does not have a 'slug' attribute.")
        return []
    res = []
    statement = sqlmodel.select(model).where(model.slug == slug)
    query_result = session.exec(statement)
    for dp in query_result:
        dp: sqlmodel.SQLModel
        res.append(dp.model_dump(mode="json"))
    return res
