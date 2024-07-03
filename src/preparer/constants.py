import os

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
ARCHIVE_APKG_ALL = "cpy-dgtmon-dev-archive-apkg-all"
IR_APKG_HTML_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-html"
IR_APKG_MD_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-md"
STATICWS_WIP_BUCKET_NAME = "cpy-dgtmon-dev-staticws-wip"

FIELD_DIGITAL_SOURCE = "digitalsrc"
FIELD_PAPER_SOURCE = "papersrc"
FIELD_DELETE_PREVIOUS = "deleteprev"
METADATA_FIELDS = [
    {
        "key": "author",
        "is_bool": False,
        "is_required": False,
        "aliases": ["authors"],
        "desc": "",
    },
    {
        "key": FIELD_DIGITAL_SOURCE,
        "is_bool": False,
        "is_required": True,
        "aliases": ["digitalsource"],
        "desc": "",
    },
    {
        "key": FIELD_PAPER_SOURCE,
        "is_bool": False,
        "is_required": True,
        "aliases": ["papersource"],
        "desc": "",
    },
    {
        "key": "original",
        "is_bool": False,
        "is_required": False,
        "aliases": ["orig", "og"],
        "desc": "",
    },
    {
        "key": "licensename",
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
        "required": False,
        "aliases": [
            "deleteprevious",
            "removeprev",
            "removeprevious",
        ],
        "desc": "",
    },
]
