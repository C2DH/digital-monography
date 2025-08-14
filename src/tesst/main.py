import logging
import os
import sys

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


# try:
#     from src._common.constants import COLOR_PAPER_ONLY
# except ModuleNotFoundError:
#     from constants import COLOR_PAPER_ONLY
from src._common.constants import COLOR_PAPER_ONLY
from mymodule import SOME_VAR

# except (ImportError, ModuleNotFoundError):
#     from .constants import COLOR_PAPER_ONLY

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler():
    assert COLOR_PAPER_ONLY == "cyan"
    assert SOME_VAR == "ahoj"
    return {"statusCode": 200}
