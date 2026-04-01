import sqlmodel

from src._common.constants import DB_URL

db_engine = sqlmodel.create_engine(DB_URL)
