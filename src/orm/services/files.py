def get_number_from_filename(s: str) -> int:
    """Extract `int(1)` from file name '01_book_chapter'."""
    number = ""
    default = -1
    for ch in s:
        if number and not ch.isdigit():
            return int(number)
        elif ch.isdigit():
            number += ch
    try:
        return int(number)
    except ValueError:
        return default
