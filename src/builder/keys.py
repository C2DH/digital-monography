import pathlib
from functools import cached_property

DEFAULT_SFS_DIR = "/mnt/efs"


class KeyPath(type(pathlib.Path())):
    _abs_root = DEFAULT_SFS_DIR

    def __new__(cls, *pathsegments):
        return super().__new__(cls, *pathsegments)

    @property
    def efs_filepath(self) -> "KeyPath":
        """Returns /mnt/efs/my-slug/path/to/file.txt"""
        return KeyPath(self._abs_root) / self

    @cached_property
    def efs_slug_dir(self) -> "KeyPath":
        """Returns /mnt/efs/my-slug"""
        return KeyPath(pathlib.Path(self._abs_root) / self.slug)

    @cached_property
    def s3_key(self) -> "KeyPath":
        """Returns my-slug/path/to/file.txt"""
        try:
            return KeyPath(self.relative_to(self._abs_root))
        except ValueError:
            return KeyPath(self)

    @cached_property
    def slug(self) -> str:
        return self.s3_key.parts[0]
