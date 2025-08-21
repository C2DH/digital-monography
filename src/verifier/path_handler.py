import pathlib
from functools import cached_property

from src._common.constants import DEFAULT_SFS_DIR


SUPPORTED_SUFFIXES = (
    # img formats
    ".jpg",
    ".jpeg",
    ".tiff",
    ".png",
    # audio/video formats
    ".mp4",
    # web formats
    ".js",
    ".css",
    # data formats
    ".json",
    ".csv",
    ".xls",
    ".xlsx",
)


class PathHandler:
    def __init__(self, fp: str, slug: str):
        self._fp = fp
        self.slug = slug
        self._windows_path = pathlib.PureWindowsPath(fp)
        self._posix_path = pathlib.PurePosixPath(fp)
        if len(self._windows_path.parts) != len(self._posix_path.parts):
            self.fp = pathlib.Path(*self._windows_path.parts)
        else:
            self.fp = pathlib.Path(fp)

    def is_relative(self) -> bool:
        return not self.fp.is_absolute() and not self._windows_path.is_absolute()

    def is_dir(self) -> bool:
        return self.exists() and self.fp.is_dir()

    def exists(self) -> bool:
        return self.efs_slug_filepath.exists()

    def is_in_asset_dir(self) -> bool:
        return self.fp.is_relative_to("assets")

    def is_suffix_supported(self) -> bool:
        return self.fp.suffix.lower() in SUPPORTED_SUFFIXES

    @cached_property
    def efs_slug_filepath(self) -> pathlib.Path:
        fp = pathlib.Path(DEFAULT_SFS_DIR) / self.slug
        for part in self.fp.parts:
            fp = fp / part
        return fp

    def __str__(self) -> str:
        return str(self.fp)
