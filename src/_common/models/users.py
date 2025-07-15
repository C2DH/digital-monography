import datetime
import sqlalchemy as sa

from ._base import Base


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime, server_default=sa.sql.func.now())

    def __repr__(self):
        return (
            f"<User(id={self.id}, "
            "first_name={self.first_name}, last_name={self.last_name}, "
            "email={self.email})>"
        )

