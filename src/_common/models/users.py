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
    __hash__ = (
        object.__hash__
    )  # Otherwise Python 3 implicitly set __hash__ to None if we override __eq__.

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

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return self.is_active

    @property
    def is_anonymous(self):
        return False

    def get_id(self) -> str:
        return str(self.id)

    def __eq__(self, other: "User") -> bool:
        """Checks the equality of two Users using `get_id`."""
        if isinstance(other, User):
            return self.get_id() == other.get_id()
        raise NotImplementedError("Cannot compare User with non-User type.")

    def __ne__(self, other: "User") -> bool:
        """Checks the inequality of two Users using `get_id`."""
        equal = self.__eq__(other)
        if equal is NotImplemented:
            raise NotImplementedError("Cannot compare User with non-User type.")
        return not equal
