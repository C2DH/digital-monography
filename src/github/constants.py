import os

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
ARCHIVE_APKG_ALL = "cpy-dgtmon-dev-archive-apkg-all"
GITHUB_SECRET_ID = "dgtmon-dev-github-api-secrets"
