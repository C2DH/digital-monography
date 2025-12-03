import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_BUILD_DIR_1 = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_book" / "_build" / "html"
JB_BUILD_DIR_2 = (
    KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "split-to-multiple-chapters" / "_build" / "html"
)


class TestIfJupyterBookV2WasCorrectlyBuild:

    @pytest.mark.parametrize(
        "url_path, dist_dir",
        [
            ("a", JB_BUILD_DIR_1),
            ("b", JB_BUILD_DIR_1),
            # ("c", JB_BUILD_DIR_1),
            # ("d", JB_BUILD_DIR_1),
            ("conditional-rendering", JB_BUILD_DIR_1),
            ("infile", JB_BUILD_DIR_2),
            ("is-unicode-with-custom-file-name", JB_BUILD_DIR_2),
        ],
    )
    def test_html_file_exist(self, url_path: str, dist_dir: KeyPath):
        assert (dist_dir / url_path / "index.html").exists()
        assert (dist_dir / url_path).with_suffix(".json").exists()
