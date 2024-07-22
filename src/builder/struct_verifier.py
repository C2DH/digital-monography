import datetime
import pathlib
import yaml
import typing as t

try:
    from .keys import KeyPath
    from .warnings import VerifierMessages
except Exception as e:
    from keys import KeyPath
    from warnings import VerifierMessages

    # from src.verifier.keys import KeyPath
    # from src.verifier.warnings import VerifierMessages


STRUCT = "file_structure"
MSG_PROBLEMS = {
    STRUCT: {
        "check_toc_missing": "",
        "check_config_missing": "",
        "check_f_in_toc_but_not_in_dir": "",
        "check_f_in_dir_but_not_in_toc": "",
    },
}


class StructVerifier:
    def __init__(self) -> None:
        self._messages = VerifierMessages()

    def summary(self):
        pass

    def stats(self):
        pass

    def verify(self, key: KeyPath, timestamp: datetime.datetime) -> VerifierMessages:
        self._timestamp = timestamp
        self._slug = key.slug
        # self._apply_metadatatables_verification()

        if self._check_toc_missing(key):
            self._messages.add_msg(
                problem=MSG_PROBLEMS[STRUCT]["check_toc_missing"],
                recommend=f"",
                timestamp=self._timestamp,
                tags=[STRUCT],
            )
        if self._check_config_missing(key):
            self._messages.add_msg(
                problem=MSG_PROBLEMS[STRUCT]["check_config_missing"],
                recommend=f"",
                timestamp=self._timestamp,
                tags=[STRUCT],
            )
        toc = self._get_toc(key.efs_slug_dir)
        toc_files = self._get_toc_file_list(toc)
        dir_files = self._get_root_level_file_list(key.efs_slug_dir)
        if self._check_f_in_toc_but_not_in_dir(toc_files, dir_files):
            self._messages.add_msg(
                problem=MSG_PROBLEMS[STRUCT]["check_f_in_toc_but_not_in_dir"],
                recommend=f"",
                timestamp=self._timestamp,
                tags=[STRUCT],
            )
        if self._check_f_in_dir_but_not_in_toc(toc_files, dir_files):
            self._messages.add_msg(
                problem=MSG_PROBLEMS[STRUCT]["check_f_in_dir_but_not_in_toc"],
                recommend=f"",
                timestamp=self._timestamp,
                tags=[STRUCT],
            )
        return self._messages

    def _get_toc(self, key: KeyPath):
        with open(key / "_toc.yml", "r") as f:
            toc = yaml.safe_load(f)
        return toc

    def _get_toc_file_list(self, toc: dict[str, t.Any]) -> list[str]:
        """
        Extract file names from table of contents structure.
        Table of contents can have a following structure:
        {'format': 'jb-book',
        'root': 'index',
        'chapters': [{'file': 'verify_h_a_cap'},
        {'file': 'verify_tables_assets',
        'sections': [{'file': 'path/to/chapter2/section1'}]}]}

        - OR -

        {'chapters': [{'file': 'verify_h_a_cap'}, {'file': 'verify_tables_assets'}],
        'format': 'jb-book',
        'root': 'index'}
        """
        file_list = []
        for chapter in toc.get("chapters", []):
            file = chapter.get("file")
            if file is not None:
                file_list.append(file)
            for section in chapter.get("sections", []):
                file = section.get("file")
                if file is not None:
                    file_list.append(file)
        return file_list

    def _get_root_level_file_list(self, key: KeyPath) -> list[pathlib.Path]:
        return [f for f in key.glob("*.*") if f.suffix.lower() in [".md", ".ipynb"]]

    def _check_toc_missing(self, key: KeyPath) -> bool:
        return not (key.efs_slug_dir / "_toc.yml").exists()

    def _check_config_missing(self, key: KeyPath) -> bool:
        return not (key.efs_slug_dir / "_config.yml").exists()

    def _check_f_in_toc_but_not_in_dir(
        self, toc_files: list[str], dir_files: list[pathlib.Path]
    ) -> list[str]:
        missing = []
        dir_files_stems = [f.stem for f in dir_files]
        for f in toc_files:
            if f not in dir_files_stems:
                missing.append(f)
        return missing

    def _check_f_in_dir_but_not_in_toc(
        self, toc_files: list[str], dir_files: list[pathlib.Path]
    ) -> list[str]:
        missing = []
        for f in dir_files:
            if f.stem not in toc_files:
                missing.append(f.name)
        return missing
