# import boto3
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
    def send(self, dynamodb: t.Any) -> None:
        if dynamodb is None:
            return
        table = dynamodb.Table(DYNAMODB_AUDIT_TBL)
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
            }
        )
