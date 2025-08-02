import bs4
import datetime
import pathlib
import typing as t
import uuid

try:
    from metadata import DocumentMetadata, RefDatapoint, TargetDatapoint
    from models import Ref, RefService, Target
    from state import DocumentState
    from keys import KeyPath
    from verif_warnings import MessagesJson, VerifierMessages
    from html2md import convert_to_md
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, RefDatapoint, TargetDatapoint
    from .models import Ref, RefService, Target
    from .state import DocumentState
    from .keys import KeyPath
    from .verif_warnings import MessagesJson, VerifierMessages
    from .html2md import convert_to_md


class BookVerifier:
    def __init__(self) -> None:
        self._messages = VerifierMessages()
        self._book_metadata: t.Dict[str, DocumentState] = {}

    def to_json(self, md: bool = False) -> MessagesJson:
        return self._messages.to_json(md)

    def sort(self) -> None:
        self._messages.sort(key=lambda msg: (msg["line"], msg["pos"]))

    def verify(self, key: KeyPath, timestamp: datetime.datetime) -> VerifierMessages:
        # self._parse_metadata(key)
        return self._messages


# TODO: add filename in RefDatapoint and TargetDatapoint cls
# centralize warnings schema in _common/_models.py
# centralize VerifierMessages <== add Warning model


LINKS = "links"
MSG_PROBLEMS = {
    LINKS: {
        "check_a_is_not_https": "Links should point to websites using secure https over http.",
        "check_a_not_archived": "Links should point to websites archived using the Internet Archive.",
        "check_a_is_invalid_infile_link": "Link points to a non-existing target.",
        "check_a_is_invalid_f2f": "Link points to a non-existing target.",
        "check_a_f2f_filename_is_invalid": "Link points a non-existing file.",
        "check_a_f2f_filename_is_absolute": "Links to targets in separate files should use absolute paths.",
        "check_a_without_hash_or_http": "Found an unspecified problem with a link.",
    }
}


class RefsAndTargetsVerifier:
    def __init__(self) -> None:
        self._targets: dict[str, tuple[pathlib.PurePath, Target]] = {}
        self._timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self._book_metadata: dict[str, DocumentState] = {}
        self._messages: list[dict[str, str]] = []
        # TODO: self._messages: list[Warning] = []

    def verify(
        self,
        book_metadata: dict[str, DocumentState],
        # targets: dict[str, tuple[pathlib.PurePath, TargetDatapoint]],
    ) -> list[dict[str, str]]:
        # mark targets
        self._book_metadata = book_metadata
        # self._book_metadata_stemmed_filenames = [m for m in self._book_metadata]
        # self._targets = targets
        for fn, dstate in self._book_metadata.items():
            targets: list[Target] = dstate["targets"]
            for target in targets:
                self._targets[target.pk] = (fn, target)
        # iterate over refs, matching them with targets
        i = 0
        for fn, dstate in self._book_metadata.items():
            for ref in dstate["refs"]:
                ref: Ref
                i += 1
                self.md_elem = ""
                if RefService.is_external(ref.href):
                    self._verify_external_links(ref)
                elif RefService.is_internal_infile(ref.href):
                    self._verify_internal_infile_links(ref)
                elif RefService.is_internal_f2f(ref.href):
                    self._verify_internal_f2f_links(ref)
                else:
                    check = "check_a_without_hash_or_http"
                    self._markwownify_html_elem(ref)
                    self._messages.append(
                        {
                            "id": uuid.uuid4().hex[:8],
                            "check": check,
                            "problem": MSG_PROBLEMS[LINKS][check],
                            "recommend": f'Hyperlink "`{ref.prev_string}`" to "`{ref.prev_href}`" is not valid. \
                                "If this is a link to an external website, it should start with "`https://`". " \
                                "If this is a hyperlink to some other part of the manuscript, read the Guidelines on writing valid references.',
                            "curr_elem": ref.elem,
                            "fn": ref.fn,
                            "timestamp": self._timestamp,
                            "tags": [LINKS],
                        }
                    )
        return self._messages

    def _verify_external_links(self, ref: Ref) -> None:
        if self._check_a_is_not_https(ref.href):
            check = "check_a_is_not_https"
            self._markwownify_html_elem(ref)
            recommend = f'The problem lies in the "`{ref.prev_string}`" link to "`{ref.prev_href}`".'
            if "http:" in ref.href:
                recommend += f' If possible, change "`{ref.prev_href}`" to "{ref.prev_href.replace('http:', 'https:', 1)}".'
            else:
                recommend += f' When possible, link to websites like "`https://example.com`" instead of "`http://example.com`".'
            self._messages.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "check": check,
                    "problem": MSG_PROBLEMS[LINKS][check],
                    "recommend": recommend,
                    "curr_elem": ref.elem,
                    "fn": ref.fn,
                    "timestamp": self._timestamp,
                    "tags": [LINKS],
                }
            )
        if self._check_a_not_archived(ref.href):
            check = "check_a_not_archived"
            self._markwownify_html_elem(ref)
            self._messages.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "check": check,
                    "problem": MSG_PROBLEMS[LINKS][check],
                    "recommend": (
                        f'The link "`{ref.prev_string}`" points to unarchived source. '
                        'Go to the "https://web.archive.org/", archive the website '
                        f'and replace "`{ref.prev_href}`" in your manuscript with a link '
                        "to the archived source."
                    ),
                    "curr_elem": ref.elem,
                    "fn": ref.fn,
                    "timestamp": self._timestamp,
                    "tags": [LINKS],
                }
            )

    def _verify_internal_infile_links(self, ref: Ref) -> None:
        target_dp = self._targets.get(ref.href[1:])
        if self._check_a_is_invalid_infile_link(target_dp):
            check = "check_a_is_invalid_infile_link"
            self._markwownify_html_elem(ref)
            ref_stem = ref.fn.split(".")[0] if "." in ref.fn else ref.fn
            self._messages.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "check": check,
                    "problem": MSG_PROBLEMS[LINKS][check],
                    "recommend": (
                        f'No matching target has been found in the "{ref_stem}" file. '
                        f'Link "`{ref.prev_string}`" points to "`{ref.prev_href}`", '
                        "but no such target has been found in the same file. "
                        "Check the Guidelines on writing correct references."
                    ),
                    "curr_elem": ref.elem,
                    "fn": ref.fn,
                    "timestamp": self._timestamp,
                    "tags": [LINKS],
                }
            )

    def _verify_internal_f2f_links(self, ref: Ref) -> None:
        target_fn, fragment = ref.href.split("#")
        target_dp = self._targets.get(fragment)
        target_stem = pathlib.Path(target_fn).stem
        if self._check_a_f2f_filename_is_absolute(target_fn):
            check = "check_a_f2f_filename_is_absolute"
            self._markwownify_html_elem(ref)
            self._messages.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "check": check,
                    "problem": MSG_PROBLEMS[LINKS][check],
                    "recommend": (
                        f'Link "`{ref.prev_string}`" points to a target using absolute path '
                        f'("`{ref.prev_href}`") instead of relative. This is not permitted '
                        "as it will lead to breaking "
                        "of the links whenever someone changes their location. "
                        "The correct link should mention the name of the file "
                        "without the folders in which this file is located. "
                        'For example, "`03_myfile.docx#heading`" is correct while '
                        '"`C:/Documents/mybook/03_myfile.docx#heading`" is not.'
                    ),
                    "curr_elem": ref.elem,
                    "fn": ref.fn,
                    "timestamp": self._timestamp,
                    "tags": [LINKS],
                }
            )
        elif self._check_a_f2f_filename_is_invalid(target_fn):
            check = "check_a_f2f_filename_is_invalid"
            self._markwownify_html_elem(ref)
            self._messages.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "check": check,
                    "problem": MSG_PROBLEMS[LINKS][check],
                    "recommend": (
                        f'Link "`{ref.prev_string}`" points to a target in "{target_stem}", '
                        "but no such file has been found. Make sure the name of the "
                        "file in this link is up to date."
                    ),
                    "curr_elem": ref.elem,
                    "fn": ref.fn,
                    "timestamp": self._timestamp,
                    "tags": [LINKS],
                }
            )
        elif self._check_a_is_invalid_f2f(target_dp):
            check = "check_a_is_invalid_f2f"
            self._markwownify_html_elem(ref)
            self._messages.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "check": check,
                    "problem": MSG_PROBLEMS[LINKS][check],
                    "recommend": (
                        f'No matching target has been found in the "{target_stem}" file. '
                        f'Link "`{ref.prev_string}`" points to "`{ref.prev_href}`", '
                        f'but no such target has been found in "{target_stem}". '
                        "Check the Guidelines on writing correct references."
                    ),
                    "curr_elem": ref.elem,
                    "fn": ref.fn,
                    "timestamp": self._timestamp,
                    "tags": [LINKS],
                }
            )

    def _markwownify_html_elem(self, ref: Ref) -> None:
        if self.md_elem != "":
            return self.md_elem
        soup = bs4.BeautifulSoup(ref.elem, "html.parser")
        self.md_elem = convert_to_md(soup)

    ################## checks ##################

    def _check_a_is_not_https(self, href: str) -> bool:
        return not href.startswith("https://")

    def _check_a_not_archived(self, href: str) -> bool:
        return href.startswith("http") and not href.startswith(
            "https://web.archive.org/"
        )

    def _check_a_is_invalid_infile_link(self, target: t.Optional[Target]) -> bool:
        return target is None

    def _check_a_is_invalid_f2f(self, target: t.Optional[Target]) -> bool:
        return target is None

    def _check_a_f2f_filename_is_invalid(self, target_fn: str) -> bool:
        p = pathlib.Path(target_fn)
        return p.stem not in [m for m in self._book_metadata]
        # return p.stem not in self._book_metadata_stemmed_filenames

    def _check_a_f2f_filename_is_absolute(self, target_fn: str) -> bool:
        check_idx = len("./")
        return "/" in target_fn[check_idx:] or "\\" in target_fn[check_idx:]
