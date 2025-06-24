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
