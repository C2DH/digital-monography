# ===== IMPORTANT =====
# Remember, the only source of truth for constants are ones defined in
# `src/_common/constants.py`. Constants defined in other directories in
# the src/ folder should be replaced with `src/_common/constants.py` before
# building the image. We advise that you always build the containers
# using Makefile commands, as the copy command is already included.
# ======================

import os
import enum


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


IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
AWS_ACCOUNT_ID = "367031255351"
AWS_ACCOUNT_REGION = "eu-west-1"
GITHUB_SECRET_ID = "dgtmon-dev-github-api-secrets"
DROPBOX_SECRET_ID = "dgtmon-dev-github-api-secrets"
DYNAMODB_TOKENS_TBL = "dgtmon-dev-dyndb-tokens-tbl"
DYNAMODB_CURSORS_TBL = "dgtmon-dev-dyndb-cursors-tbl"
# dynamodb table for publisher to manage content
DYNAMODB_AUDIT_TBL = "dgtmon-dev-dyndb-audit-tbl"
DYNAMODB_ALERTS_TBL = "dgtmon-dev-dyndb-alerts-tbl"
DYNAMODB_LOGINS_TBL = "dgtmon-dev-dyndb-logins-tbl"
DYNAMODB_ASSETS_TBL = "dgtmon-dev-dyndb-assets-tbl"  # migrate from and stop using
DYNAMODB_CITATIONS_TBL = "dgtmon-dev-dyndb-citations-tbl"
DYNAMODB_HEADINGS_TBL = "dgtmon-dev-dyndb-headings-tbl"
DYNAMODB_WARNINGS_TBL = "dgtmon-dev-dyndb-warnings-tbl"
DYNAMODB_ASSETS_DOC_INFO_TBL = "dgtmon-dev-dyndb-assets-doc-info-tbl"
DYNAMODB_ASSETS_UPLOAD_INFO_TBL = "dgtmon-dev-dyndb-assets-upload-info-tbl"
DYNAMODB_ASSETS_BOOK_INFO_TBL = "dgtmon-dev-dyndb-assets-book-info-tbl"
# SQS queues
SQS_GITHUB_TRIGGER_NAME = "cpy-dgtmon-dev-github-trigger"
SQS_GITHUB_FIFO_TRIGGER_NAME = "cpy-dgtmon-dev-github-trigger.fifo"
SQS_BUILDER_TRIGGER_NAME = "cpy-dgtmon-dev-builder-trigger"
SQS_BUILDER_FIFO_TRIGGER_NAME = "cpy-dgtmon-dev-builder-trigger.fifo"
# S3 bucket names
# ARCHIVE_APKG_ALL = "cpy-dgtmon-dev-archive-apkg-all"
APKG_UPLOAD_BUCKET_NAME = "cpy-dgtmon-dev-apkg-upload"
IR_APKG_HTML_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-html"
IR_APKG_MD_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-md"
STATICWS_WIP_BUCKET_NAME = "cpy-dgtmon-dev-staticws-wip"
STATICWS_DASHBOARD_BUCKET_NAME = "cpy-dgtmon-dev-staticws-dashboard"
METADATA_ASSETS_BUCKET_NAME = "cpy-dgtmon-dev-metadata-assets"
METADATA_REFS_BUCKET_NAME = "cpy-dgtmon-dev-metadata-refs"
VERIFIER_MSGS = "cpy-dgtmon-dev-verifier-msgs"
# API endpoints
BE_PATH_ASSET_METADATA = "assets-metadata"
BE_PATH_ASSET_UPLOAD = "assets-s3-list"
BE_PATH_ASSET_RETRIEVE = "asset-retrieve"
BE_PATH_REF_METADATA = "refs-metadata"
# python-mammoth options
MAMMOTH_STYLE_MAP = """
p[style-name='Quote'] => blockquote:fresh
p[style-name='Caption'] => p.dgt-mon-caption:fresh
highlight[color='lightGray'] => span.dgt-mon-digital-only
highlight[color='cyan'] => span.dgt-mon-paper-only
"""
# html classes
CLS_METADATA_TABLE = "dgt-mon-metadata-table"
CLS_METADATA_TABLE_JSONDATA = "dgt-mon-hidden-metadata"
ATTRIB_METADATA_UUID = "dgt-mon-metadata-uuid"
# caption types
CAPTION_ITEM_TYPE_FIGURE = "fig"
CAPTION_ITEM_TYPE_TABLE = "tbl"
CAPTION_ITEM_TYPE_GRAPH = "graph"
CAPTION_ITEM_TYPE_OTHER = "oth"
# metadata fields
FIELD_DIGITAL_SOURCE = "digitalinput"
FIELD_PAPER_SOURCE = "paperinput"
FIELD_DELETE_PREVIOUS = "deleteprevious"
FIELD_LICENSE_NAME = "license"
METADATA_FIELDS = [
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
# status management fields
STATUS_MGMT_FIELDS = [
    # metadata fields, be sure to correspond with METADATA_FIELDS
    {
        "key": "author",
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": FIELD_DIGITAL_SOURCE,
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": FIELD_PAPER_SOURCE,
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": "original",
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": FIELD_LICENSE_NAME,
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": "licenseurl",
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": "alttext",
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": FIELD_DELETE_PREVIOUS,
        "type": "BOOL",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": "uuid",
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    # read only fields
    {
        "key": "filesize",
        "type": "N",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    {
        "key": "filetype",
        "type": "S",
        "is_read_only": True,
        "rel": "one_to_one",
    },
    # misc
    {
        "key": "status",
        "type": "N",  # TODO: make some enum to set the status
        "is_read_only": False,
        "rel": "one_to_one",
        # "rel": "many_to_one",
    },
    {
        "key": "tags",
        "type": "L",
        "is_read_only": False,
        "rel": "many_to_one",
        "children": [
            {
                "key": "tag",
                "type": "S",
                "is_read_only": False,
            },
        ],
    },
    {
        "key": "comments",
        "type": "L",
        "is_read_only": False,
        "rel": "many_to_one",
        "children": [
            {
                "key": "date",
                "type": "S",
                "is_read_only": True,
            },
            {
                "key": "comment",
                "type": "S",
                "is_read_only": True,
            },
        ],
    },
    {
        "key": "desc",
        "type": "S",
        "is_read_only": False,
        "rel": "one_to_one",
    },
]
