import pytest

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.keys import KeyPath

JB_BUILD_DIR = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / "a_book" / "_build" / "html"


class TestWorkflowFromDocxToJupyterBookV2:

    @pytest.mark.parametrize(
        "url_path",
        [
            "a",
            "b",
            "c",
            "d",
            "conditional-rendering",
        ],
    )
    def test_html_file_exist(self, url_path: str):
        assert (JB_BUILD_DIR / url_path / "index.html").exists()
        assert (JB_BUILD_DIR / url_path).with_suffix(".json").exists()
