from src._common.models import ConfigService
from src._common.keys import KeyPath


class TestConfigHandling:
    split_cfg_key = (
        KeyPath("tests") / "_fixtures" / "split-to-multiple-chapters" / "myst.yml"
    )

    def test_load_config__split(self):
        cfg = ConfigService.load_from_file(self.split_cfg_key)
        print("self.cfg", cfg)
        print("cfg.site", cfg.site)
        print("cfg.project", cfg.project)
        assert cfg.project["title"] == "Split Document Example"
        assert len(cfg.project["authors"]) == 2
        assert cfg.project["authors"][0]["name"] == "Pawel Kaminski"
        assert (
            cfg.project["authors"][0]["affiliations"]
            == "Luxembourg Centre for Contemporary and Digital History (C²DH)"
        )
        assert cfg.site["template"] == "book-theme"
        assert cfg.dgtmon.autonumber == "chapters"
