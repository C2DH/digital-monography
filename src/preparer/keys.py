import typing as t

try:
    from .constants import DEFAULT_SFS_DIR
except Exception as e:
    from constants import DEFAULT_SFS_DIR


class InvalidKey(Exception):
    pass


class Key:
    def __init__(self, key: str, is_upload: bool):
        self._input_str = key
        self._is_upload = is_upload
        self._parts = self._input_str.replace("\\", "/").split("/")
        self._validate_input_str()
        if self._is_upload:
            self.root = ""
            self.phase = ""
            self.slug = self._shift_parts()
            self.path = "/".join(self._parts)
            self.filename = self._parts[-1]
        else:
            self.root = self._shift_parts()
            self.phase = self._shift_parts()
            self.slug = self._shift_parts()
            self.path = "/".join(self._parts)
            self.filename = self._parts[-1]

    def _validate_input_str(self) -> None:
        if self._is_upload and len(self._parts) < 2:
            raise InvalidKey(
                f"Missing parts of the key {self._input_str}. "
                + "Key is too short: it can be either "
                + "'my-slug/path/to/file.xx' or 'my-slug/file.xx'"
            )
        elif self._is_upload == False and len(self._parts) < 4:
            raise InvalidKey(
                f"Missing parts of the key {self._input_str}. "
                + "Key is too short: it can be either "
                + "'my-root/my-phase/my-slug/file.xx' or "
                + "'my-root/my-phase/my-slug/path/to/file.xx'"
            )

    def _shift_parts(self) -> str:
        val = self._parts[0]
        del self._parts[0]
        return val

    def with_suffix(self, suffix: str) -> "Key":
        if not suffix.startswith("."):
            raise ValueError("Key suffix should start with a '.' dot, e.g. '.html'.")
        if "." not in self.filename and self._is_upload:
            return Key("/".join([self.slug, self.path + suffix]), self._is_upload)
        elif "." not in self.filename:
            return Key(
                "/".join([self.root, self.phase, self.slug, self.path + suffix]),
                self._is_upload,
            )
        fn = self.filename
        for i in range(len(fn)):
            backward_idx = len(fn) - i - 1
            if fn[backward_idx] == ".":
                fn = self.filename[0:backward_idx] + suffix
                break
        new_path = self.path.replace(self.filename, fn)
        if self._is_upload:
            key = "/".join([self.slug, new_path])
        else:
            key = "/".join([self.root, self.phase, self.slug, new_path])
        return Key(key, is_upload=self._is_upload)

    def as_input_dir(self, suffix: t.Optional[str] = None) -> "Key":
        root = self.root if self.root else DEFAULT_SFS_DIR
        key = "/".join([root, "input", self.slug, self.path])
        if suffix:
            return Key(key, is_upload=False).with_suffix(suffix)
        return Key(key, is_upload=False)

    def as_html_dir(self, suffix: t.Optional[str] = None) -> "Key":
        root = self.root if self.root else DEFAULT_SFS_DIR
        key = "/".join([root, "html", self.slug, self.path])
        if suffix:
            return Key(key, is_upload=False).with_suffix(suffix)
        return Key(key, is_upload=False)

    def as_md_dir(self, suffix: t.Optional[str] = None) -> "Key":
        root = self.root if self.root else DEFAULT_SFS_DIR
        key = "/".join([root, "md", self.slug, self.path])
        if suffix:
            return Key(key, is_upload=False).with_suffix(suffix)
        return Key(key, is_upload=False)

    def as_jb_dir(self, suffix: t.Optional[str] = None) -> "Key":
        root = self.root if self.root else DEFAULT_SFS_DIR
        key = "/".join([root, "jb", self.slug, self.path])
        if suffix:
            return Key(key, is_upload=False).with_suffix(suffix)
        return Key(key, is_upload=False)

    def __str__(self):
        if self._is_upload:
            return "/".join([self.slug, self.path])
        else:
            return "/".join([self.root, self.phase, self.slug, self.path])
