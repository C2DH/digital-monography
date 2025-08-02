from models import Substitution
from constants import AUTONUMBER_PLACEHOLDER


def get_substitution_for_digital_version(subst: Substitution, file_prefix=None) -> str:
    """
    Returns the value that will replace placeholder, e.g. `1.I`.
    Used for substituting values in builder (for digital version).
    """
    if subst.is_digital is False and subst.is_paper is True:
        return ""
    elif subst.new_item_num and file_prefix:
        return f"{file_prefix}.{subst.prefix}{subst.new_item_num}"
    elif subst.new_item_num is not None:
        file_count = subst.file_count if subst.file_count is not None else ""
        return f"{file_count}.{subst.prefix}{subst.new_item_num}"
    elif subst.was == AUTONUMBER_PLACEHOLDER:
        return ""
    else:
        return subst.was
