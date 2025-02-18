import datetime
import pathlib
import typing as t
import uuid

try:
    from metadata import DocumentMetadata, RefDatapoint, TargetDatapoint
    from keys import KeyPath
    from verif_warnings import MessagesJson, VerifierMessages
except (ImportError, ModuleNotFoundError):
    from .metadata import DocumentMetadata, RefDatapoint, TargetDatapoint
    from .keys import KeyPath
    from .verif_warnings import MessagesJson, VerifierMessages


class BookVerifier:
    def __init__(self) -> None:
        self._messages = VerifierMessages()
        self._metadatas: t.Dict[str, DocumentMetadata] = {}

    def to_json(self, md: bool = False) -> MessagesJson:
        return self._messages.to_json(md)

    def sort(self) -> None:
        self._messages.sort(key=lambda msg: (msg["line"], msg["pos"]))

    def verify(self, key: KeyPath, timestamp: datetime.datetime) -> VerifierMessages:
        # self._parse_metadata(key)
        return self._messages


# TODO: add filename in RefDatapoint and TargetDatapoint cls
# centralize warnings schema in _common/_models.py
# centralize VerifierMessages


LINKS = "links"
MSG_PROBLEMS = {
    LINKS: {
        "check_a_is_not_https": "Links should point to websites using secure https over http.",
        "check_a_not_archived": "Links should point to websites archived using the Internet Archive.",
        "check_a_is_invalid_infile_link": "Link points to a non-existing target.",
        "check_a_is_invalid_f2f": "Link points to a non-existing target.",
        "check_a_f2f_filename_is_invalid": "Link points a non-existing file.",
        "check_a_f2f_filename_is_absolute": "Links to targets in separate files should use absolute paths.",
        "check_a_has_hash_or_http": "Found an unspecified problem with a link.",
    }
}


class RefsAndTargetsVerifier:
    def __init__(self) -> None:
        self._targets: dict[str, tuple[pathlib.PurePath, TargetDatapoint]] = {}
        self._timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self._metadatas: dict[pathlib.PurePath, DocumentMetadata] = {}
        self._messages: list[dict[str, str]] = []
        # TODO: self._messages: VerifierMessages = VerifierMessages()

    def verify(
        self, multidocs_meta: dict[pathlib.PurePath, DocumentMetadata]
    ) -> list[dict[str, str]]:
        # mark targets
        # self._fp_stems: set[str] = set()
        self._metadatas = multidocs_meta
        for fn, meta in self._metadatas.items():
            # self._fp_stems.add(ref_stem)
            for target in meta.targets:
                target: TargetDatapoint
                self._targets[target.pk] = (fn, target)
        #         print(f"target.pk={target.pk}, fn={fn}, target={target}")
        # print("=" * 100)
        # print("=" * 100)
        # iterate over refs, matching them with targets
        i = 0
        for fn, md in self._metadatas.items():
            for ref in md.refs:
                i += 1
                ref: RefDatapoint
                try:
                    ref_stem = ref.fn.split(".")[0]
                except IndexError:
                    ref_stem = ref.fn
                print("ref", ref, ref_stem)
                # 1. if href is external, perform verification
                if ref.href.startswith("http") and ".sharepoint.com/" not in ref.href:
                    # print(i, "External link:", ref.href)
                    if self._check_a_is_not_https(ref.href):
                        recommend = f'The problem lies in the "`{ref.prev_string}`" link to "`{ref.prev_href}`".'
                        if "http:" in ref.href:
                            recommend += f' If possible, change "`{ref.prev_href}`" to "{ref.prev_href.replace('http:', 'https:', 1)}".'
                        else:
                            recommend += f' When possible, link to websites like "`https://example.com`" instead of "`http://example.com`".'
                        self._messages.append(
                            {
                                "id": uuid.uuid4().hex[:8],
                                "problem": MSG_PROBLEMS[LINKS]["check_a_is_not_https"],
                                "recommend": recommend,
                                "elem": str(ref.elem),
                                "fn": ref.fn,
                                "timestamp": self._timestamp,
                                "tags": [LINKS],
                            }
                        )
                    if self._check_a_not_archived(ref.href):
                        self._messages.append(
                            {
                                "id": uuid.uuid4().hex[:8],
                                "problem": MSG_PROBLEMS[LINKS]["check_a_not_archived"],
                                "recommend": (
                                    f'The link "`{ref.prev_string}`" points to unarchived source. '
                                    'Go to the "https://web.archive.org/", archive the website '
                                    f'and replace "`{ref.prev_href}`" in your manuscript with a link '
                                    "to the archived source."
                                ),
                                "elem": str(ref.elem),
                                "fn": ref.fn,
                                "timestamp": self._timestamp,
                                "tags": [LINKS],
                            }
                        )
                # 2. if href points to the same doc, check targets of this file
                elif ref.href.startswith("#"):
                    target_dp = self._targets.get(ref.href[1:])
                    # print(i, "In-file link:", ref.href, target_dp)
                    if self._check_a_is_invalid_infile_link(target_dp):
                        self._messages.append(
                            {
                                "id": uuid.uuid4().hex[:8],
                                "problem": MSG_PROBLEMS[LINKS][
                                    "check_a_is_invalid_infile_link"
                                ],
                                "recommend": (
                                    f'No matching target has been found in the "{ref_stem}" file. '
                                    f'Link "`{ref.prev_string}`" points to "`{ref.prev_href}`", '
                                    "but no such target has been found in the same file. "
                                    "Check the Guidelines on writing correct references."
                                ),
                                "elem": str(ref.elem),
                                "fn": ref.fn,
                                "timestamp": self._timestamp,
                                "tags": [LINKS],
                            }
                        )
                # 3. if href points to another doc, check targets of that file
                elif "#" in ref.href:
                    target_fn, fragment = ref.href.split("#")
                    target_dp = self._targets.get(fragment)
                    target_stem = pathlib.Path(target_fn).stem
                    # print(i, "Cross-file link:", ref.href, target_dp)
                    # print("fragment", fragment)

                    # target_dp

                    if self._check_a_f2f_filename_is_absolute(target_fn):
                        self._messages.append(
                            {
                                "id": uuid.uuid4().hex[:8],
                                "problem": MSG_PROBLEMS[LINKS][
                                    "check_a_f2f_filename_is_absolute"
                                ],
                                "recommend": (
                                    f'Link "`{ref.prev_string}`" points to a target using absolute path '
                                    "instead of relative. This is not permitted as it will lead to breaking "
                                    "of the links whenever someone changes their location. "
                                    "The correct link should mention the name of the file "
                                    "without the folders in which this file is located. "
                                    'For example, "`03_myfile.docx#heading`" is correct while'
                                    '"`C:/Documents/mybook/03_myfile.docx#heading`" is not.'
                                ),
                                "elem": str(ref.elem),
                                "fn": ref.fn,
                                "timestamp": self._timestamp,
                                "tags": [LINKS],
                            }
                        )
                    elif self._check_a_f2f_filename_is_invalid(target_fn):
                        # print("\t\t\t>>")
                        # print("\n\t\t >>> target_fn", target_fn)
                        # print("\n\t\t >>> target_fn", target_fn)
                        # print(multidocs_meta.keys())
                        # print("self._fp_stems", self._fp_stems)
                        self._messages.append(
                            {
                                "id": uuid.uuid4().hex[:8],
                                "problem": MSG_PROBLEMS[LINKS][
                                    "check_a_f2f_filename_is_invalid"
                                ],
                                "recommend": (
                                    f'Link "`{ref.prev_string}`" points to a target in "{target_stem}", '
                                    "but no such file has been found. Make sure the name of the "
                                    "file in this link is up to date."
                                ),
                                "elem": str(ref.elem),
                                "fn": ref.fn,
                                "timestamp": self._timestamp,
                                "tags": [LINKS],
                            }
                        )
                    elif self._check_a_is_invalid_f2f(target_dp):
                        self._messages.append(
                            {
                                "id": uuid.uuid4().hex[:8],
                                "problem": MSG_PROBLEMS[LINKS][
                                    "check_a_is_invalid_f2f"
                                ],
                                "recommend": (
                                    f'No matching target has been found in the "{target_stem}" file. '
                                    f'Link "`{ref.prev_string}`" points to "`{ref.prev_href}`", '
                                    f'but no such target has been found in "{target_stem}". '
                                    "Check the Guidelines on writing correct references."
                                ),
                                "elem": str(ref.elem),
                                "fn": ref.fn,
                                "timestamp": self._timestamp,
                                "tags": [LINKS],
                            }
                        )

                else:
                    # print(i, "Unknown link:", ref.href)
                    self._messages.append(
                        {
                            "id": uuid.uuid4().hex[:8],
                            "problem": MSG_PROBLEMS[LINKS]["check_a_has_hash_or_http"],
                            "recommend": f'Hyperlink "`{ref.prev_string}`" to "`{ref.prev_href}`" is not valid. \
                                "If this is a link to an external website, it should start with "`https://`". " \
                                "If this is a hyperlink to some other part of the manuscript, read the Guidelines on writing valid references.',
                            "elem": str(ref.elem),
                            "fn": ref.fn,
                            "timestamp": self._timestamp,
                            "tags": [LINKS],
                        }
                    )
        return self._messages

    def _check_a_is_not_https(self, href: str) -> bool:
        return not href.startswith("https://")

    def _check_a_not_archived(self, href: str) -> bool:
        return href.startswith("http") and not href.startswith(
            "https://web.archive.org/"
        )

    def _check_a_is_invalid_infile_link(
        self, target: t.Optional[TargetDatapoint]
    ) -> bool:
        return target is None

    def _check_a_is_invalid_f2f(self, target: t.Optional[TargetDatapoint]) -> bool:
        return target is None

    def _check_a_f2f_filename_is_invalid(self, target_fn: str) -> bool:
        p = pathlib.Path(target_fn)
        return p.stem not in self._metadatas.keys()

    def _check_a_f2f_filename_is_absolute(self, target_fn: str) -> bool:
        check_idx = len("./")
        return "/" in target_fn[check_idx:] or "\\" in target_fn[check_idx:]
