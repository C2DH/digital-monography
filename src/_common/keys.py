import pathlib
from functools import cached_property

try:
    from constants import DEFAULT_SFS_DIR, JB_DIR, PAPER_DIR, STATE_DIR, INPUT_DIR
except (ImportError, ModuleNotFoundError):
    from .constants import DEFAULT_SFS_DIR, JB_DIR, PAPER_DIR, STATE_DIR, INPUT_DIR  # type: ignore


class InvalidKey(Exception):
    pass


domain_dirs = [
    JB_DIR,
    PAPER_DIR,
    STATE_DIR,
    INPUT_DIR,
]


class KeyPath(type(pathlib.Path())):  # type: ignore
    """
    Abstraction over `pathlib.Path` to handle files in local and EFS file systems.
    Note:
        - No files should be stored directly in the abs_root directory.
        - When running locally, s3 buckets are simulated as a subdirectories of abs_root.
          Interaction with them should be done via s3 client faker and not via KeyPath directly.
        - It is still open whether _STATE_DIR should be a domain directory.
        - It is still open whether some file processing (e.g. changing format to json)
          should be a KeyPath method or run outside of KeyPath.
        - Methods ending with `_path` return full paths to files,
          while methods ending with `_dir` return paths to directories.

    A usual KeyPath consists of the following elements:
        `abs_root / domain / slug / path`
    where
        - `abs_root` is the absolute root directory, e.g. /mnt/efs or /tmp/efs
        - `domain` is one of the domain directories (e.g. _JB, _PAPER, _STATE, _INPUT)
        - `slug` is the unique book identifier
        - `path` is the relative path to a file within a book (e.g. chapter1.md, assets/image.png)
    """

    domain_dirs = [INPUT_DIR, JB_DIR, PAPER_DIR, STATE_DIR]

    def __new__(cls, *pathsegments):
        return super().__new__(cls, *pathsegments)

    def __truediv__(self, new_part: str) -> "KeyPath":
        """Overriding the '/' operator to return a KeyPath object"""
        return KeyPath(super().__truediv__(new_part))

    @property
    def abs_root(self) -> "KeyPath":
        """Returns the absolute root directory for the KeyPath."""
        return KeyPath(DEFAULT_SFS_DIR)

    @cached_property
    def s3_key(self) -> "KeyPath":
        """Returns my-slug/path/to/file.txt"""
        try:
            parts = self.relative_to(self.abs_root).parts
            if parts[0] in self.domain_dirs:
                return KeyPath(*parts[1:])
            return KeyPath(*parts)
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

    # dirs

    @cached_property
    def efs_jb_dir(self) -> "KeyPath":
        """Returns /mnt/efs/_JB/my-slug"""
        return self.abs_root / JB_DIR / self.slug

    @cached_property
    def efs_paper_dir(self) -> "KeyPath":
        """Returns /mnt/efs/_PAPER/my-slug"""
        return self.abs_root / PAPER_DIR / self.slug

    @cached_property
    def efs_state_dir(self) -> "KeyPath":
        """Returns /mnt/efs/_STATE/my-slug"""
        return self.abs_root / STATE_DIR / self.slug

    @cached_property
    def efs_input_dir(self) -> "KeyPath":
        """Returns /mnt/efs/_INPUT/my-slug"""
        return self.abs_root / INPUT_DIR / self.slug

    # paths

    @cached_property
    def efs_jb_path(self) -> "KeyPath":
        """Returns /mnt/efs/_JB/my-slug/path/to/file.txt"""
        return self.efs_jb_dir / self.github_path

    @cached_property
    def efs_paper_path(self) -> "KeyPath":
        """Returns /mnt/efs/_PAPER/my-slug/path/to/file.txt"""
        # print("self.efs_paper_dir", self.efs_paper_dir)
        return self.efs_paper_dir / self.github_path

    @cached_property
    def efs_state_path(self) -> "KeyPath":
        """Returns /mnt/efs/_STATE/my-slug/path/to/file.txt"""
        # print("self.efs_state_dir", self.efs_state_dir)
        return self.efs_state_dir / self.github_path

    @cached_property
    def efs_input_path(self) -> "KeyPath":
        """Returns /mnt/efs/_INPUT/my-slug/path/to/file.txt"""
        return self.efs_input_dir / self.github_path

    # legacy

    @property
    def efs_filepath(self) -> "KeyPath":
        """Returns /mnt/efs/_INPUT/my-slug/path/to/file.txt"""
        # """Returns /mnt/efs/my-slug/path/to/file.txt"""
        # TODO: remove, illegal
        # return self.abs_root / self
        return self.efs_input_path

    @cached_property
    def efs_slug_dir(self) -> "KeyPath":
        """Returns /mnt/efs/_INPUT/my-slug"""
        # """Returns /mnt/efs/my-slug"""
        # TODO: remove, illegal
        return self.efs_input_dir
        # return self.abs_root / self.slug

    @cached_property
    def efs_slug_html_path(self) -> "KeyPath":
        """Adds '_html' in slug, /mnt/efs/my-slug/_html/path/to/file.txt"""
        # TODO: remove
        return self._add_to_efs_slug_dir("_html")

    @cached_property
    def efs_slug_metadata_path(self) -> "KeyPath":
        # TODO: not used, make stuff use it
        """Adds '_metadata' in slug, /mnt/efs/my-slug/_metadata/path/to/file.txt"""
        # TODO: remove
        return self._add_to_efs_slug_dir("_metadata")

    @cached_property
    def efs_slug_paper_path(self) -> "KeyPath":
        """Adds '_paper' in slug, /mnt/efs/my-slug/_paper/path/to/file.txt"""
        # TODO: remove
        return self._add_to_efs_slug_dir("_paper")

    @cached_property
    def efs_slug_jb_path(self) -> "KeyPath":
        """Adds '_jb' in slug, /mnt/efs/my-slug/_jb/path/to/file.txt"""
        # TODO: remove
        return self._add_to_efs_slug_dir("_jb")

    @cached_property
    def efs_slug_warnings_path(self) -> "KeyPath":
        """Adds '_warnings' in slug, /mnt/efs/my-slug/_warnings/path/to/file.txt"""
        # TODO: remove
        return self._add_to_efs_slug_dir("_warnings")

    def _add_to_efs_slug_dir(self, fldr: str) -> "KeyPath":
        """Adds <fldr> folder to slug dir, /mnt/efs/my-slug/<fldr>/path/to/file.txt"""
        if not (self.efs_slug_dir / fldr).exists():
            (self.efs_slug_dir / fldr).mkdir(parents=True)
        return self.efs_slug_dir / fldr / self.github_path
