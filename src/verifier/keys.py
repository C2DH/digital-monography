# ===== IMPORTANT =====
# Remember, the only source of truth for keys.py is the one defined in
# `src/_common/keys.py`. KeyPaths defined in other directories in
# the src/ folder should be replaced with `src/_common/keys.py` before
# building the image. We advise that you always build the containers
# using Makefile commands, as the copy command is already included.
# ======================

import pathlib
from functools import cached_property

try:
    from .constants import DEFAULT_SFS_DIR
except Exception as e:
    from constants import DEFAULT_SFS_DIR


class InvalidKey(Exception):
    pass


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
    def github_path(self) -> "KeyPath":
        """Returns path/to/file.txt (without my-slug)"""
        try:
            for i, part in enumerate(self.parts):
                if part == self.slug:
                    return KeyPath(*self.parts[i + 1 :])
            return KeyPath(self)
        except ValueError:
            return KeyPath(self)

    @cached_property
    def slug(self) -> str:
        """Returns my-slug"""
        return self.s3_key.parts[0]

    @cached_property
    def efs_slug_html_path(self) -> "KeyPath":
        """Adds '_html' in slug, /mnt/efs/my-slug/_html/path/to/file.txt"""
        return self.add_to_efs_slug_dir("_html")

    def add_to_efs_slug_dir(self, fldr: str) -> "KeyPath":
        """Adds <fldr> folder to slug dir, /mnt/efs/my-slug/<fldr>/path/to/file.txt"""
        if not (self.efs_slug_dir / fldr).exists():
            self.efs_slug_dir.mkdir(fldr)
        return self.efs_slug_dir / fldr / self.github_path
