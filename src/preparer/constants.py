# ===== IMPORTANT =====
# Remember, the only source of truth for constants are ones defined in
# `src/_common/constants.py`. Constants defined in other directories in
# the src/ folder should be replaced with `src/_common/constants.py` before
# building the image. We advise that you always build the containers
# using Makefile commands, as the copy command is already included.
# ======================

import os

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
GITHUB_SECRET_ID = "dgtmon-dev-github-api-secrets"
DROPBOX_SECRET_ID = "dgtmon-dev-github-api-secrets"
DYNAMODB_TOKENS_TBL = "dgtmon-dev-dyndb-tokens-tbl"
DYNAMODB_CURSORS_TBL = "dgtmon-dev-dyndb-cursors-tbl"
# S3 bucket names
ARCHIVE_APKG_ALL = "cpy-dgtmon-dev-archive-apkg-all"
APKG_UPLOAD_BUCKET_NAME = "cpy-dgtmon-dev-apkg-upload"
IR_APKG_HTML_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-html"
IR_APKG_MD_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-md"
STATICWS_WIP_BUCKET_NAME = "cpy-dgtmon-dev-staticws-wip"
VERIFIER_MSGS = "cpy-dgtmon-dev-verifier-msgs"
# html classes
CLS_METADATA_TABLE = "dgt-mon-metadata-table"
CLS_METADATA_TABLE_JSONDATA = "dgt-mon-hidden-metadata"
ATTRIB_METADATA_UUID = "dgt-mon-metadata-uuid"
# metadata fields
FIELD_DIGITAL_SOURCE = "digitalsource"
FIELD_PAPER_SOURCE = "papersource"
FIELD_DELETE_PREVIOUS = "deleteprevious"
FIELD_LICENSE_NAME = "licensename"
METADATA_FIELDS = [
    {
        "key": "author",
        "is_bool": False,
        "is_required": False,
        "aliases": ["authors", "autor", "autors"],
        "desc": "",
    },
    {
        "key": FIELD_DIGITAL_SOURCE,
        "is_bool": False,
        "is_required": True,
        "aliases": ["digitalsrc", "digital"],
        "desc": "",
    },
    {
        "key": FIELD_PAPER_SOURCE,
        "is_bool": False,
        "is_required": True,
        "aliases": ["papersrc", "paper"],
        "desc": "",
    },
    {
        "key": "original",
        "is_bool": False,
        "is_required": False,
        "aliases": ["orig", "og", "origin"],
        "desc": "",
    },
    {
        "key": FIELD_LICENSE_NAME,
        "is_bool": False,
        "is_required": True,
        "aliases": ["license"],
        "desc": "",
    },
    {
        "key": "licenseurl",
        "is_bool": False,
        "is_required": False,
        "aliases": [],
        "desc": "",
    },
    {
        "key": "alttext",
        "is_bool": False,
        "is_required": True,
        "aliases": ["alt"],
        "desc": "",
    },
    {
        "key": FIELD_DELETE_PREVIOUS,
        "is_bool": True,
        "is_required": False,
        "aliases": [
            "deleteprev",
            "removeprev",
            "removeprevious",
        ],
        "desc": "",
    },
    {
        "key": "uuid",
        "is_bool": False,
        "is_required": False,
        "aliases": [],
        "desc": "Automatic UUID of the metadata table.",
    },
]
METADATA_FIELDS_KEYS = []
for field in METADATA_FIELDS:
    METADATA_FIELDS_KEYS.append(field["key"])
    METADATA_FIELDS_KEYS.extend(field["aliases"])
