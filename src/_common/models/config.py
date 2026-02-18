import dataclasses
import datetime
import enum
import typing as t
import yaml

try:
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ..keys import KeyPath  # type: ignore


##################################
# NOTE: Is it common or maybe just builder-specific?
# If the latter, move it to builder.
##################################


class ConfigAuthor(t.TypedDict, total=False):
    """https://mystmd.org/guide/frontmatter#frontmatter-authors"""

    name: t.Any  # a TODO string OR CSL-JSON author object
    id: str | None = None
    orcid: str | None = None
    corresponding: bool | None = None
    email: str | None = None
    roles: list[str] | None = None
    # TODO: a list of strings or a full Affiliation object
    affiliations: list[str | dict] | None = None
    equal_contributor: bool | None = None
    deceased: bool | None = None
    note: str | None = None
    phone: str | None = None
    fax: str | None = None
    url: str | None = None


class ConfigProject(t.TypedDict, total=False):
    authors: list[ConfigAuthor | str] = []
    open_access: bool = True
    date: str = datetime.date.today().isoformat()


class ConfigSite(t.TypedDict, total=False):
    template: str = "book-theme"


class AutonumberOptions(enum.StrEnum):
    SKIP = "skip"  # skip autonumbering and leave as written in source file
    BOOK = "book"  # increment autonumbering across the whole book
    CHAPTERS = "chapters"  # reset autonumbering at the start of each chapter


@dataclasses.dataclass
class ConfigDgtmon:
    autonumber: AutonumberOptions = dataclasses.field(
        default=AutonumberOptions.CHAPTERS
    )


@dataclasses.dataclass
class Config:
    """
    Representation of the Jupyter Book v2 configuration + custom dgtmon fields.
    See mystmd docs: https://mystmd.org/guide/configuration
    """

    version: int = 1
    dgtmon: ConfigDgtmon = dataclasses.field(default_factory=ConfigDgtmon)
    project: ConfigProject = dataclasses.field(default_factory=ConfigProject)
    site: ConfigSite = dataclasses.field(default_factory=ConfigSite)

    def to_yaml(self) -> str:
        """Serialize config object into a YAML string. Use instead of `yaml.safe_dump`."""

        def _normalize_for_yaml(obj: t.Any) -> t.Any:
            """Recursively convert `enum.Enum` members to plain values for YAML.

            PyYAML may emit python-specific tags for Enum objects; converting
            them to their `.value` (strings) ensures portable, plain YAML.
            """
            if isinstance(obj, enum.Enum):
                return obj.value
            if isinstance(obj, dict):
                return {k: _normalize_for_yaml(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_normalize_for_yaml(v) for v in obj]
            return obj

        data = _normalize_for_yaml(dataclasses.asdict(self))
        return yaml.safe_dump(data, sort_keys=False)


class ConfigService:

    @staticmethod
    def load_from_file(key: KeyPath) -> Config:
        with open(key, "r") as f:
            prev_cfg = yaml.safe_load(f)
            if not isinstance(prev_cfg, dict):
                prev_cfg = {}
            cfg = Config(**prev_cfg)
            cfg.dgtmon = ConfigDgtmon(**prev_cfg.get("dgtmon", {}))
            return cfg
        return Config()

    @staticmethod
    def find_config_file(key: KeyPath) -> KeyPath | None:
        potential_files = ["myst.yml", "myst.yaml"]
        for fn in potential_files:
            config_fp = key.efs_jb_dir / fn
            if config_fp.exists():
                return config_fp
        return None

    @staticmethod
    def save_myst_config(key: KeyPath, cfg: Config) -> None:
        potential_files = ["myst.yml", "myst.yaml"]
        for fn in potential_files:
            config_fp = key.efs_jb_dir / fn
            if not config_fp.exists():
                continue
            with open(config_fp, "w") as f:
                f.write(cfg.to_yaml())
            return
        with open(key.efs_jb_dir / potential_files[0], "w") as f:
            f.write(cfg.to_yaml())
