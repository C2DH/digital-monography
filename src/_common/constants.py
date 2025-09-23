# ===== IMPORTANT =====
# Remember, the only source of truth for constants are ones defined in
# `src/_common/constants.py`. Constants defined in other directories in
# the src/ folder should be replaced with `src/_common/constants.py` before
# building the image. We advise that you always build the containers
# using Makefile commands, as the copy command is already included.
# ======================

import os
import enum
import typing as t


class ModuleEnum(enum.Enum):
    ENTRYPOINT = 10
    DROPBOX = 20
    PREPARER = 30
    VERIFIER = 40
    GITHUB = 60
    BUILDER = 70
    GPU = 80


class MediumEnum(enum.StrEnum):
    PAPER = "P"
    DIGITAL = "D"
    PAPER_AND_DIGITAL = "P+D"


class S3Event(enum.StrEnum):
    OBJ_CREATED = "ObjectCreated"
    OBJ_REMOVED = "ObjectRemoved"


class DgtmonSecrets(t.TypedDict):
    github_api_token: str
    github_api_org: str
    dropbox_app_secret: str


IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
JB_DIR = "_JB"
PAPER_DIR = "_PAPER"
STATE_DIR = "_STATE"
ASSETS_DIR = "assets"
# database
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_path = os.environ.get("DB_PATH", DEFAULT_SFS_DIR + "/_database.db")
db_driver = os.environ.get("DB_DRIVER", "sqlite")
if db_user and db_pass:
    DB_URL = "{}://{}:{}@/{}".format(db_driver, db_user, db_pass, db_path)
else:
    DB_URL = "{}:///{}".format(db_driver, db_path)
# API endpoints
BE_PATH_ASSET_METADATA = "assets-metadata"
BE_PATH_ASSET_UPLOAD = "assets-s3-list"
BE_PATH_ASSET_RETRIEVE = "asset-retrieve"
BE_PATH_REF_METADATA = "refs-metadata"
# python-mammoth options
COLOR_DIGITAL_ONLY = "lightGray"
COLOR_PAPER_ONLY = "cyan"
CLS_DIGITAL_ONLY = "dgt-mon-digital-only"
CLS_PAPER_ONLY = "dgt-mon-paper-only"
CLS_CAPTION = "dgt-mon-caption"
MAMMOTH_STYLE_MAP = f"""
p[style-name='Quote'] => blockquote:fresh
p[style-name='Caption'] => p.{CLS_CAPTION}:fresh
highlight[color='{COLOR_DIGITAL_ONLY}'] => span.{CLS_DIGITAL_ONLY}
highlight[color='{COLOR_PAPER_ONLY}'] => span.{CLS_PAPER_ONLY}
"""
# frontmatter fields
FM_FIELD_FRONTMATTER_KEYPATH = "frontmatter_key"
FM_FIELD_IS_SPLIT = "_split"
FM_FIELD_TOC = "_toc"
# html classes
CLS_FRONTMATTER_TABLE = "dgt-mon-frontmatter-table"
CLS_METADATA_TABLE = "dgt-mon-metadata-table"
CLS_METADATA_TABLE_JSONDATA = "dgt-mon-hidden-metadata"
CLS_STATE_TABLE_JSONDATA = "dgt-mon-hidden-state"
ATTRIB_METADATA_UUID = "dgt-mon-metadata-uuid"
# docx constants
AUTONUMBER_PLACEHOLDER = "[auto]"
# caption types
CAPTION_ITEM_TYPE_FIGURE = "fig"
CAPTION_ITEM_TYPE_TABLE = "tbl"
CAPTION_ITEM_TYPE_GRAPH = "graph"
CAPTION_ITEM_TYPE_OTHER = "oth"
CAPTION_ALLOWED_ITEMS = ["figure", "fig", "table", "graph"]
# metadata fields
FIELD_DIGITAL_SOURCE = "digitalinput"
FIELD_PAPER_SOURCE = "paperinput"
FIELD_DELETE_PREVIOUS = "deleteprevious"
FIELD_LICENSE_NAME = "license"
MetadataFieldType = t.TypedDict(
    "MetadataFieldType",
    {
        "key": str,
        "is_bool": bool,
        "is_required": bool,
        "aliases": list[str],
        "show": str,
        "desc": str,
    },
)
METADATA_FIELDS: list[MetadataFieldType] = [
    {
        "key": "id",
        "is_bool": False,
        "is_required": True,
        "aliases": ["identifier"],
        "show": "## Id",
        "desc": "Manual ID of the asset. Does not have to be unique.",
    },
    {
        "key": "author",
        "is_bool": False,
        "is_required": False,
        "show": "## Authors",
        "aliases": ["authors", "autor", "autors", "institution", "inst"],
        "desc": "Attribute an author of an object. Institution could also be attributed.",
    },
    {
        "key": FIELD_DIGITAL_SOURCE,
        "is_bool": False,
        "is_required": True,
        "show": "## Digital input",
        "aliases": ["digitalsource", "digitalsrc", "digital"],
        "desc": r"Path to a file that will be displayed in a digital version of a book. Path should point to a location where the file is saved in the `assets` folder. Be careful to write a correct relative path to the file, e.g. `./assets/path/to/file.png` is valid while `C:\User\Documents\my-book\assets\path\to\file.png` is an invalid.",
    },
    {
        "key": FIELD_PAPER_SOURCE,
        "is_bool": False,
        "is_required": False,
        "show": "## Paper input",
        "aliases": ["papersource", "papersrc", "paper"],
        "desc": r"Path to a file that will be displayed in a paper version of a book. Path should point to a location where the file is saved in the `assets` folder. Be careful to write a correct relative path to the file, e.g. `./assets/path/to/file.png` is valid while `C:\User\Documents\my-book\assets\path\to\file.png` is an invalid. If left empty, no object will not be included in the duplicate.",
    },
    {
        "key": FIELD_LICENSE_NAME,
        "is_bool": False,
        "is_required": False,
        "show": "## License",
        "aliases": ["licensename"],
        "desc": "Name of a license under which an object was published. Preferably [SPDX ID](https://spdx.org/licenses/) like “BSD-4-Clause”. A full name, e.g. “Creative Commons Attribution 4.0 International”, is also acceptable, although not recommended.",
    },
    {
        "key": "source",
        "is_bool": False,
        "is_required": True,
        "show": "## Source",
        "aliases": ["credit"],
        "desc": "All relevant source and copyright information.",
    },
    {
        "key": "alttext",
        "is_bool": False,
        "is_required": True,
        "show": "## Alt text",
        "aliases": ["alt"],
        "desc": "Alt text to describe appearance or function of a multimedia object.",
    },
    {
        "key": "iscolor",
        "is_bool": True,
        "is_required": False,
        "show": "## Is color",
        "aliases": ["color", "colour", "iscolour"],
        "desc": "Indicate whether an asset is meant to be printed in color. If a figure should be printed in black-and-white, leave it empty or write “no”.",
    },
    {
        "key": FIELD_DELETE_PREVIOUS,
        "is_bool": True,
        "is_required": False,
        "show": "## Delete previous",
        "aliases": [
            "deleteprev",
            "removeprev",
            "removeprevious",
        ],
        "desc": "Use this field if you want to remove previous object, like image, video, etc. Useful when you want to have an image directly in your MS Word file and replace it with an image indicated with “##Digital-source” or “##Paper-source”.",
    },
    {
        "key": "comments",
        "is_bool": False,
        "is_required": False,
        "show": "## Comments",
        "aliases": ["comment"],
        "desc": "In case MS Word comments are not enough, you can comment an asset using this field so that this comment is visible in editor’s internal tools.",
    },
    {
        "key": "isready",
        "is_bool": True,
        "is_required": False,
        "show": "## Is ready",
        "aliases": ["ready", "ok", "isok"],
        "desc": "Mark this asset as viewed in editor’s internal tools. This field is reserved for editors.",
    },
    {
        "key": "uuid",
        "is_bool": False,
        "is_required": False,
        "show": "## Uuid",
        "aliases": [],
        "desc": "Automatic UUID of the metadata table.",
    },
]
METADATA_FIELDS_KEYS = []
for field in METADATA_FIELDS:
    METADATA_FIELDS_KEYS.append(field["key"])
    METADATA_FIELDS_KEYS.extend(field["aliases"])
