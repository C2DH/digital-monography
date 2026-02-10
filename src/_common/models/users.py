import sqlmodel
from werkzeug import security as wkzg_security

try:
    from constants import UserRole
except (ImportError, ModuleNotFoundError):
    from ..constants import UserRole  # type: ignore


class User(sqlmodel.SQLModel, table=True):
    """
    App-level db model does not need to inherit from BookSQLModel nor ChapterSQLModel.
    """

    __tablename__ = "users"

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    username: str = sqlmodel.Field(index=True, nullable=False, unique=True)
    password_hash: str = sqlmodel.Field()
    role: UserRole = sqlmodel.Field(default=UserRole.Author, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = wkzg_security.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return wkzg_security.check_password_hash(self.password_hash, password)

    # TODO: maybe make it into service function?
    def has_role(self, role_name: str) -> bool:
        return self.role == role_name
