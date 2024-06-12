import os

IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    DEFAULT_SFS_DIR = "/tmp/efs"  # local execution
else:
    DEFAULT_SFS_DIR = "/mnt/efs"  # AWS EFS
STATICWS_WIP_BUCKET_NAME = "cpy-dgtmon-dev-staticws-wip"
