import dataclasses
import datetime
import enum
import os
import typing as t

# try:
#     from constants import DYNAMODB_LOGINS_TBL
# except (ImportError, ModuleNotFoundError):
#     from .constants import DYNAMODB_LOGINS_TBL


class LoginStatus(enum.Enum):
    FAILED = 0
    AUTHENTICATED = 1


@dataclasses.dataclass
class LoginEvent:
    trace_id: str
    status: int
    timestamp: datetime.datetime = dataclasses.field(init=False)

    def __post_init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def send(self, dynamodb: t.Any) -> t.Any:
        if dynamodb is None:
            return
        table = dynamodb.Table(os.environ.get("DYNAMODB_LOGINS_TBL", ""))
        expire_at = int(
            (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=4)
            ).timestamp()
        )  # 4 hours is the Dropbox token expiration time
        table.put_item(
            Item={
                "timestamp": self.timestamp,
                "status": self.status,
                "trace_id": self.trace_id,
                "expire_at": expire_at,
            }
        )

    def __str__(self):
        return "Alert(slug={self.slug}, status={self.status})"
