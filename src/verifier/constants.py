import os

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
# ARCHIVE_APKG_ALL = "cpy-dgtmon-dev-archive-apkg-all"
# IR_APKG_HTML_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-html"
# IR_APKG_MD_BUCKET_NAME = "cpy-dgtmon-dev-ir-apkg-md"
# STATICWS_WIP_BUCKET_NAME = "cpy-dgtmon-dev-staticws-wip"
