# ===== IMPORTANT =====
# Remember, the only source of truth for github_trigger.py is the one defined in
# `src/_common/github_trigger.py`. Objects defined in other directories in
# the src/ folder should be replaced with `src/_common/github_trigger.py` before
# building the image.
# ======================
import dataclasses
import enum
import json

try:
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath  # type: ignore


class GithubActionEnum(enum.StrEnum):
    DELETE_OBJECT = "del"
    UPDATE_OBJECT = "put"


@dataclasses.dataclass
class GithubTriggerMsg:
    """
    Represents a body of a SQS message.
    This message is enqueued from microservices that want to trigger
    the src/github microservice.

    You can read more about sending and receiving SQS messages in the docs.
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/sqs-example-sending-receiving-msgs.html
    """

    key: KeyPath
    action: GithubActionEnum

    def dumps(self) -> dict[str, str]:
        return json.dumps(
            {
                "key": str(self.key),
                "action": self.action.value,
            }
        )

    @staticmethod
    def loads(json_str: str) -> "GithubTriggerMsg":
        data = json.loads(json_str)
        return GithubTriggerMsg(
            key=KeyPath(data["key"]),
            action=GithubActionEnum(data["action"]),
        )

    def deduplication_id(self) -> str:
        return f"{self.action.value}::{self.key}"

    @property
    def slug(self) -> str:
        return self.key.slug
