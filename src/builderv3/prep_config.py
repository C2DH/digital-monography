import datetime
import logging
import typing as t
import yaml

from src._common.keys import KeyPath
from src._common.models import Config, ConfigService
from src._common.state import BookState


type LegacyConfig = dict[str, t.Any]


def init_myst_config(key: KeyPath, bookstate: BookState) -> None:
    config_key = ConfigService.find_config_file(key)
    if config_key is None:
        bookstate.config = Config()
    else:
        bookstate.config = ConfigService.load_from_file(config_key)
    ConfigService.save_myst_config(config_key, bookstate.config)


# def _find_myst_config_file(key: KeyPath) -> KeyPath | None:
#     potential_files = ["myst.yml", "myst.yaml"]
#     for fn in potential_files:
#         config_key = key.efs_jb_dir / fn
#         if config_key.exists():
#             return config_key
#     return None


# legacy


def create_myst_config_file(key: KeyPath) -> dict[str, t.Any]:
    """
    Generate myst.yml config file for Jupyter Book v2 build.

    Authors may want to provide their own myst config file,
    for example to set custom site.template options. Some fields
    will be overridden while creating myst config file.

    At the same time, Jupyter Book v2 requires a myst config file
    to build the book. We also want to restrict authors from
    setting certain fields in the myst config file.

    If myst returns an ENOENT error like this:
    `ENOENT: no such file or directory, lstat '_build/site/config.json'`
    this means that the myst.yml file was not generated properly.

    See docs for more info:
    https://mystmd.org/guide/frontmatter#in-a-myst-yml-file

    Docs on extending myst config:
    https://mystmd.org/guide/frontmatter#composing-myst-yml
    """
    cfg = _read_myst_config(key)
    cfg2 = _read_myst_config_new(key)
    print("\n\ncfg2", cfg2, "\n\n")
    _overwrite_myst_config_file(cfg)
    _save_myst_config_file(key, cfg)


def _read_myst_config(key: KeyPath) -> dict[str, t.Any]:
    """
    It is adviasable for authors to write their own "myst.yml".
    """
    potential_files = ["myst.yml", "myst.yaml"]
    for fn in potential_files:
        config_fp = key.efs_jb_dir / fn
        if not config_fp.exists():
            continue
        with open(config_fp, "r") as f:
            prev_cfg = yaml.safe_load(f)
            if not isinstance(prev_cfg, dict):
                logging.warning(
                    f"Previous myst config file {fn} is not a dict. Ignoring."
                )
                prev_cfg = {}
            return prev_cfg
    return {}


def _read_myst_config_new(key: KeyPath) -> Config:
    """
    It is adviasable for authors to write their own "myst.yml".
    """
    potential_files = ["myst.yml", "myst.yaml"]
    for fn in potential_files:
        config_fp = key.efs_jb_dir / fn
        if not config_fp.exists():
            continue
        with open(config_fp, "r") as f:
            prev_cfg = yaml.safe_load(f)
            if not isinstance(prev_cfg, dict):
                logging.warning(
                    f"Previous myst config file {fn} is not a dict. Ignoring."
                )
                prev_cfg = {}
            return Config(**prev_cfg)
    return Config()


def _overwrite_myst_config_file(cfg: dict[str, t.Any]) -> dict[str, t.Any]:
    """
    To be a valid myst config file for Jupyter Book v2, "myst.yml" has to have
    certain structure with version: 1 and site or project keys.
    """
    if "version" not in cfg:
        cfg["version"] = 1
    # project
    if "project" not in cfg:
        cfg["project"] = {}
    if "date" not in cfg["project"]:
        cfg["project"]["date"] = datetime.date.today().isoformat()
    cfg["project"]["open_access"] = True  # always open access
    # site
    if "site" not in cfg:
        cfg["site"] = {}
    cfg["site"]["template"] = "book-theme"
    if "options" not in cfg["site"]:
        cfg["site"]["options"] = {}
    cfg["site"]["options"]["folders"] = True
    return cfg


def _save_myst_config_file(key: KeyPath, cfg: dict[str, t.Any]) -> None:
    potential_files = ["myst.yml", "myst.yaml"]
    for fn in potential_files:
        config_fp = key.efs_jb_dir / fn
        if not config_fp.exists():
            continue
        with open(config_fp, "w") as f:
            f.write(yaml.dump(cfg))
        return
    with open(key.efs_jb_dir / potential_files[0], "w") as f:
        f.write(yaml.dump(cfg))
