import dataclasses
import datetime
import enum
import typing as t

try:
    from constants import DYNAMODB_AUDIT_TBL
except (ImportError, ModuleNotFoundError):
    from .constants import DYNAMODB_AUDIT_TBL


class AuditStatus(enum.Enum):
    FAILED = 0
    PENDING = 1
    SUCCESS = 2


@dataclasses.dataclass
class AuditEvent:
    slug: str
    timestamp: datetime.datetime
    module: int
    filename: str
    status: int
    msg: str

    # db: t.Union[boto3.resources.base.ServiceResource, Faker]
    # -> dynamodb put_item response
    def send(self, dynamodb: t.Any) -> t.Any:
        if dynamodb is None:
            return
        table = dynamodb.Table(DYNAMODB_AUDIT_TBL)
        expire_at = int(
            (datetime.datetime.now() + datetime.timedelta(days=30)).timestamp()
        )  # NOTE: if you want to archive the audit trail, disable TTL feature""
        table.put_item(
            Item={
                "slug": self.slug,
                "module": self.module,
                "event": {
                    "timestamp": self.timestamp,
                    "filename": self.filename,
                    "status": self.status,
                    "msg": self.msg,
                },
                "expire_at": expire_at,
            }
        )

    def __str__(self):
        return (
            "AuditEvent("
            f"slug={self.slug}, "
            f"module={self.module}, "
            f"timestamp={self.timestamp}, "
            f"filename={self.filename}, "
            f"status={self.status}, "
            f"msg={self.msg}"
            ")"
        )
