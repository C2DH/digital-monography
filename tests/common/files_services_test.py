from src._common.models import FileService


def test_get_number_from_filename():
    assert FileService.get_number_from_filename("12345.docx") == 12345
    assert FileService.get_number_from_filename("01_book_chapter.docx") == 1
    assert FileService.get_number_from_filename("file_00123.txt") == 123
    assert FileService.get_number_from_filename("chapter_02.docx") == 2
    assert FileService.get_number_from_filename("01_part-2.docx") == 1
    assert FileService.get_number_from_filename("no_number.docx") == -1
