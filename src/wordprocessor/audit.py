import dataclasses
import datetime
import enum
import os
import typing as t


class AuditStatus(enum.Enum):
    FAILED = 0
    PENDING = 1
    SUCCESS = 2


@dataclasses.dataclass
class AuditEvent:
    slug: str
    timestamp: datetime.datetime = dataclasses.field(init=False)
    module: int
    filename: str
    status: int
    msg: str

    def __post_init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # db: t.Union[boto3.resources.base.ServiceResource, Faker]
    # -> dynamodb put_item response
    def send(self, dynamodb: t.Any) -> t.Any:
        if dynamodb is None:
            return
        table = dynamodb.Table(os.environ.get("DYNAMODB_AUDIT_TBL", ""))
        expire_at = int(
            (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=30)
            ).timestamp()
        )  # NOTE: if you want to archive the audit trail, disable TTL feature
        table.put_item(
            Item={
                "slug": self.slug,
                "timestamp": self.timestamp,
                "module": self.module,
                "filename": self.filename,
                "status": self.status,
                "msg": self.msg,
                "expire_at": expire_at,
            }
        )

    def __str__(self):
        return (
            "AuditEvent("
            f"slug={self.slug}, "
            f"timestamp={self.timestamp}, "
            f"module={self.module}, "
            f"filename={self.filename}, "
            f"status={self.status}, "
            f"msg={self.msg}"
            ")"
        )


############################## alerts ##############################


class AlertStatus(enum.Enum):
    START = ("started",)
    FAIL = (
        "pipeline-fail"  # pipeline encountered error and a book could not be processed
    )
    NOAUTH = ("auth-rejected",)  # rejecting a request from an unauthenticated user
    NOVERIF = ("verif-warning",)  # very important warning that should be fixed asap


@dataclasses.dataclass
class AlertLog:
    """
    Alert logs the last known status of the most important services.
    """

    slug: str
    status: str

    def send(self, dynamodb: t.Any) -> t.Any:
        if not self.slug or dynamodb is None:
            return
        table = dynamodb.Table(os.environ.get("DYNAMODB_ALERTS_TBL", ""))
        table.put_item(
            Item={
                "slug": self.slug,
                "status": self.status,
            }
        )

    def __str__(self):
        return "Alert(slug={self.slug}, status={self.status})"
