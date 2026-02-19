from src._common.models import ConfigService
from src._common.keys import KeyPath


class TestConfigHandling:
    multidoc_cfg_key = KeyPath("tests") / "_fixtures" / "a_book" / "myst.yml"
    splitdoc_cfg_key = (
        KeyPath("tests") / "_fixtures" / "split-to-multiple-chapters" / "myst.yml"
    )

    def test_load_config__splitdoc(self):
        cfg = ConfigService.load_from_file(self.splitdoc_cfg_key)
        assert cfg.project["title"] == "Split Document Example"
        assert len(cfg.project["authors"]) == 2
        assert cfg.project["authors"][0]["name"] == "Pawel Kaminski"
        assert (
            cfg.project["authors"][0]["affiliations"]
            == "Luxembourg Centre for Contemporary and Digital History (C²DH)"
        )
        assert cfg.site["template"] == "book-theme"
        assert cfg.dgtmon.per_chapter_numbering == True
        assert len(cfg.dgtmon.prefixes) == 0
        assert cfg.dgtmon.prefixes == {}

    def test_load_config__multidoc(self):
        cfg = ConfigService.load_from_file(self.multidoc_cfg_key)
        assert cfg.project["title"] == "Examples of book contents"
        assert len(cfg.project["authors"]) == 1
        assert cfg.project["authors"][0]["name"] == "Pawel Kaminski"
        assert cfg.site["template"] == "book-theme"
        assert cfg.dgtmon.per_chapter_numbering == True  # default, not in config
        assert len(cfg.dgtmon.prefixes) == 6
        assert cfg.dgtmon.prefixes["00_index"] == "I"
        assert cfg.dgtmon.prefixes["01_a"] == 1
        assert cfg.dgtmon.prefixes["02_b"] == 2
        assert cfg.dgtmon.prefixes["03_c"] == 3
        assert cfg.dgtmon.prefixes["04_d"] == 4
        assert cfg.dgtmon.prefixes["05_conditional_rendering"] == 5
