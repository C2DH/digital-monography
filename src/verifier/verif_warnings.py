import bs4
import datetime
import typing as t
import uuid

try:
    from html2md import convert_to_md
except (ImportError, ModuleNotFoundError):
    from .html2md import convert_to_md


class FileVerificationMessageJson(t.TypedDict):
    id: str
    problem: str
    recommend: str
    fn: str
    prev_elem: str
    curr_elem: str
    next_elem: str
    timestamp: str
    tags: list[str]
    line: int
    pos: int


class GeneralVerificationMessageJson(t.TypedDict):
    id: str
    problem: str
    recommend: str
    timestamp: str
    tags: list[str]
    line: int
    pos: int


class FileVerificationMessage:
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

    def __getitem__(self, x):
        """Makes object subscriptable, allowing to access e.g. message['id']"""
        return getattr(self, x)

    def copy(self) -> "FileVerificationMessage":
        return FileVerificationMessage(
            problem=self.problem,
            recommend=self.recommend,
            prev_elem=self.prev_elem,
            elem=self.curr_elem,
            next_elem=self.next_elem,
            timestamp=self.timestamp,
            fn=self.fn,
            tags=self.tags,
        )

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

    def to_json(self, md: bool = False) -> FileVerificationMessageJson:
        return {
            "id": self.id,
            "problem": self.problem,
            "recommend": self.recommend,
            "fn": self.fn,
            "prev_elem": self._bs4element_to_str(self.prev_elem, md),
            "curr_elem": self._bs4element_to_str(self.curr_elem, md),
            "next_elem": self._bs4element_to_str(self.next_elem, md),
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "line": self.line,
            "pos": self.pos,
        }

    def _bs4element_to_str(
        self, elem: t.Optional[bs4.element.PageElement], md: bool
    ) -> str:
        elem_str = str(elem)
        if not elem or elem_str == "None":
            return ""
        if isinstance(elem, bs4.element.NavigableString):
            return elem_str
        return convert_to_md(elem) if md else elem_str

    def __str__(self):
        return self.to_json()


class GeneralVerificationMessage:
    def __init__(
        self,
        problem: str,
        recommend: str,
        timestamp: datetime.datetime,
        tags: list[str],
    ) -> None:
        self.id = uuid.uuid4().hex[:8]
        self.problem = problem
        self.recommend = recommend
        self.timestamp = timestamp
        self.tags = tags
        self.line = 0
        self.pos = 0

    def __getitem__(self, x):
        """Makes object subscriptable, allowing to access e.g. message['id']"""
        return getattr(self, x)

    def copy(self) -> "GeneralVerificationMessage":
        return GeneralVerificationMessage(
            problem=self.problem,
            recommend=self.recommend,
            timestamp=self.timestamp,
            tags=self.tags,
        )

    def to_json(self, md: bool = False) -> GeneralVerificationMessageJson:
        return {
            "id": self.id,
            "problem": self.problem,
            "recommend": self.recommend,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "line": self.line,
            "pos": self.pos,
        }

    def __str__(self):
        return self.to_json()


class VerifierMessages:
    _messages: list[t.Union[FileVerificationMessage, GeneralVerificationMessage]]

    def __init__(self):
        self._messages = []

    def add_msg(
        self,
        problem: str,
        recommend: str,
        timestamp: datetime.datetime,
        tags: list[str],
        prev_elem: t.Optional[bs4.element.Tag] = None,
        elem: t.Optional[bs4.element.Tag] = None,
        next_elem: t.Optional[bs4.element.Tag] = None,
        fn: t.Optional[str] = None,
    ) -> None:
        if elem is not None:
            self._messages.append(
                FileVerificationMessage(
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
        else:
            self._messages.append(
                GeneralVerificationMessage(
                    problem=problem,
                    recommend=recommend,
                    timestamp=timestamp,
                    tags=tags,
                )
            )

    def to_json(
        self, md: bool = False
    ) -> list[t.Union[FileVerificationMessageJson, GeneralVerificationMessageJson]]:
        return [msg.to_json(md) for msg in self._messages]

    def sort(self, *args, **kwargs) -> None:
        self._messages.sort(*args, **kwargs)

    def __str__(self):
        return self.to_json()
