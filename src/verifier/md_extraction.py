import dataclasses
import errno
import os
import pathlib
import sys
import typing as t


ERROR_INVALID_NAME = 123  # Windows-specific error code indicating an invalid pathname.
# https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-

try:
    from .constants import (
        METADATA_FIELDS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
    )
except Exception as e:
    from constants import (
        METADATA_FIELDS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
    )


type AcceptedValues = t.Union[str, bool, pathlib.Path]


class FieldTypeRecord(t.TypedDict):
    key: str
    is_bool: bool
    is_required: bool
    aliases: list[str]
    desc: str


@dataclasses.dataclass
class AssetDatapoint:
    _key: str
    _val: str
    key: str = dataclasses.field(init=False)
    val: AcceptedValues = dataclasses.field(init=False)
    field: t.Optional[FieldTypeRecord] = dataclasses.field(init=False)

    def __post_init__(self):
        self.key = self._normalize_key(self._key)
        self.field = next((f for f in METADATA_FIELDS if f["key"] == self.key), None)
        if self.field is not None and self.field["is_bool"]:
            self.val = self._val_to_bool(self._val)
        elif self.key in (
            FIELD_DIGITAL_SOURCE,
            FIELD_PAPER_SOURCE,
        ) and self.is_pathname_valid(self._val):
            fp = pathlib.Path(self._val)
            self.val = fp
        # TODO: consider adding an url handler
        else:
            self.val = self._val.strip()

    # def _looks_like_a_potential_filepath(self, v: str) -> bool:
    #     # TODO: after clarity on the asset storage, change this naive
    #     # logic into `if fp.exists() and not fp.is_dir()` or similar
    #     if v.startswith("./"):
    #         return True
    #     return False

    def _normalize_key(self, s: str) -> str:
        while " " in s:
            s = s.replace(" ", "")
        s = s.lower().strip().replace("_", "").replace("-", "").replace("#", "")
        for field in METADATA_FIELDS:
            if s in field["aliases"]:
                return field["key"]
        return s

    def _val_to_bool(self, _v: str) -> bool:
        v = _v.strip().lower()
        if v in [
            "0",
            "no",
            "nee",
            "not",
            "non",
            "nul",
            "none",
            "nicht",
            "nein",
            "false",
            "kein",
        ]:
            return False
        return bool(v)

    def to_dict(self):
        return {self.key: self.val}

    def to_json(self):
        return {self.key: str(self.val)}

    def is_pathname_valid(self, pathname: str) -> bool:
        """
        `True` if the passed pathname is a valid pathname for the current OS;
        `False` otherwise.
        Kudoz to: https://stackoverflow.com/a/34102855/8007403
        """
        # If this pathname is either not a string or is but is empty, this pathname
        # is invalid.
        try:
            if not isinstance(pathname, str) or not pathname:
                return False

            # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
            # if any. Since Windows prohibits path components from containing `:`
            # characters, failing to strip this `:`-suffixed prefix would
            # erroneously invalidate all valid absolute Windows pathnames.
            _, pathname = os.path.splitdrive(pathname)

            # Directory guaranteed to exist. If the current OS is Windows, this is
            # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
            # environment variable); else, the typical root directory.
            root_dirname = (
                os.environ.get("HOMEDRIVE", "C:")
                if sys.platform == "win32"
                else os.path.sep
            )
            assert os.path.isdir(root_dirname)

            # Append a path separator to this directory if needed.
            root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

            # Test whether each path component split from this pathname is valid or
            # not, ignoring non-existent and non-readable path components.
            for pathname_part in pathname.split(os.path.sep):
                try:
                    os.lstat(root_dirname + pathname_part)
                # If an OS-specific exception is raised, its error code
                # indicates whether this pathname is valid or not. Unless this
                # is the case, this exception implies an ignorable kernel or
                # filesystem complaint (e.g., path not found or inaccessible).
                #
                # Only the following exceptions indicate invalid pathnames:
                #
                # * Instances of the Windows-specific "WindowsError" class
                #   defining the "winerror" attribute whose value is
                #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
                #   fine-grained and hence useful than the generic "errno"
                #   attribute. When a too-long pathname is passed, for example,
                #   "errno" is "ENOENT" (i.e., no such file or directory) rather
                #   than "ENAMETOOLONG" (i.e., file name too long).
                # * Instances of the cross-platform "OSError" class defining the
                #   generic "errno" attribute whose value is either:
                #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
                #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
                except OSError as exc:
                    if hasattr(exc, "winerror"):
                        if exc.winerror == ERROR_INVALID_NAME:
                            return False
                    elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                        return False
        # If a "TypeError" exception was raised, it almost certainly has the
        # error message "embedded NUL character" indicating an invalid pathname.
        except TypeError as exc:
            return False
        # If no exception was raised, all path components and hence this
        # pathname itself are valid. (Praise be to the curmudgeonly python.)
        else:
            return True
        # If any other exception was raised, this is an unrelated fatal issue
        # (e.g., a bug). Permit this exception to unwind the call stack.
