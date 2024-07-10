import bs4
import datetime
import typing as t
import uuid


class VerifierMessageJson(t.TypedDict):
    problem: str
    action: str
    fn: str
    line: int
    pos: int


class VerifierMessage:
    def __init__(
        self,
        problem: str,
        recommend: str,
        prev_elem: t.Optional[bs4.element.Tag],
        elem: bs4.element.Tag,
        next_elem: t.Optional[bs4.element.Tag],
        timestamp: datetime.datetime,
        fn: str,
        tags: list[str],
    ) -> None:
        self.id = uuid.uuid4().hex[:8]
        self.problem = problem
        self.recommend = recommend
        self.prev_elem = prev_elem if prev_elem else self.find_prev_elem(elem)
        self.curr_elem = elem
        self.next_elem = next_elem if next_elem else self.find_next_elem(elem)
        self.timestamp = timestamp
        self.fn = fn
        self.tags = tags
        self.line = elem.sourceline
        self.pos = elem.sourcepos

    @staticmethod
    def find_prev_elem(elem: bs4.element.Tag) -> t.Optional[bs4.element.PageElement]:
        """
        Find previous_sibling, ommiting empty ones.
        """
        prev = elem.previous_sibling
        for i in range(5):  # don't look for more than 5 siblings
            if hasattr(prev, "text") and prev.text.isspace():
                prev = prev.previous_sibling
            else:
                break
        return prev

    @staticmethod
    def find_next_elem(elem: bs4.element.Tag) -> t.Optional[bs4.element.PageElement]:
        """
        Find next_sibling, ommiting empty ones.
        """
        next = elem.next_sibling
        for i in range(5):  # don't look for more than 5 siblings
            if hasattr(next, "text") and next.text.isspace():
                next = next.next_sibling
            else:
                break
        return next

    def to_json(self) -> VerifierMessageJson:
        return {
            "id": self.id,
            "problem": self.problem,
            "recommend": self.recommend,
            "fn": self.fn,
            "prev_elem": str(self.prev_elem),
            "curr_elem": str(self.curr_elem),
            "next_elem": str(self.next_elem),
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "line": self.line,
            "pos": self.pos,
        }


class VerifierMessages:
    def __init__(self):
        self._messages = []

    def add_msg(
        self,
        problem: str,
        recommend: str,
        elem: bs4.element.Tag,
        fn: str,
        timestamp: datetime.datetime,
        tags: list[str],
        prev_elem: t.Optional[bs4.element.Tag] = None,
        next_elem: t.Optional[bs4.element.Tag] = None,
    ) -> None:
        self._messages.append(
            VerifierMessage(
                problem=problem,
                recommend=recommend,
                prev_elem=prev_elem,
                elem=elem,
                next_elem=next_elem,
                timestamp=timestamp,
                fn=fn,
                tags=tags,
            )
        )

    def to_json(self) -> list[VerifierMessageJson]:
        return [msg.to_json() for msg in self._messages]
