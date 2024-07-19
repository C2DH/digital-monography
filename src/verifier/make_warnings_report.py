import bs4
import datetime
import typing as t


try:
    from .warnings import FileVerificationMessageJson, GeneralVerificationMessageJson
except ModuleNotFoundError:
    from warnings import FileVerificationMessageJson, GeneralVerificationMessageJson


def make_warnings_report(
    soup: bs4.BeautifulSoup,
    json_data: list[
        t.Union[FileVerificationMessageJson, GeneralVerificationMessageJson]
    ],
    timestamp: datetime.datetime,
    fn: str,
) -> str:
    char_count, word_count = _get_character_and_word_count(soup)
    formated_date = timestamp.strftime("%A %d. %B %Y, %H:%M")
    report = f"""\
# Result of the automatic verification of "{fn}"

## Statistics

| Statistic | Value |
| --- | --- |
| Character count (no spaces) | {char_count} |
| Word count | {word_count} |
| Last update | {formated_date} |

## About automatic verification

The digital publishing platform scans the submitted manuscript
and checks each line against the predefined rules.
If an element violates a rule, the platform flags it as a warning.
Click on the drop-down to see the fragment of the manuscript where the issue was raised
as well as a description of the problem.
The "👉" character will point the exact element that has violated a rule.

## Warning messages

"""
    if len(json_data) == 0:
        report += """\
:::{note}
👍 The platform has not found any rules violated by this file.
:::
"""
    for msg in json_data:
        if msg.get("curr_elem"):
            report += _make_fwarning_dropdown(msg)
    return report


# def _make_gwarning_dropdown(msg: GeneralVerificationMessageJson) -> str:
#     return ""


def _get_character_and_word_count(soup: bs4.BeautifulSoup) -> tuple[int, int]:
    soup_contents_list = []
    for elem in soup.find_all(text=True):
        soup_contents_list.append(elem.text.strip())
    soup_contents = "".join(soup_contents_list).replace(" ", "")  # minimize spaces
    words = []
    for line in soup_contents_list:
        for word in line.split(" "):
            if word and not word.isspace():
                words.append(word)
    # # words = [line.split(" ") for line in soup_contents_list]
    # # This is a bit wasteful. To get an accurate value
    # [s.extract() for s in soup(["style", "script", "[document]", "head", "title"])]
    # visible_text = soup.getText()

    # words = re.findall("[a-zA-Z_]+", md)
    # print("\n\n\n")
    # print(
    #     ">>> visible_text ---------------\n",
    #     visible_text,
    #     len(visible_text),
    #     len(visible_text.split(" ")),
    # )
    # print(
    #     ">>> soup.text ---------------\n",
    #     soup.text,
    #     len(soup.text),
    #     len(soup.text.split(" ")),
    # )
    # print(
    #     ">>> soup.find_all(text=True) ---------------\n",
    #     soup_contents,
    #     len(soup_contents),
    #     len(words),
    #     words,
    # )
    # print("\n\n\n")
    # # # TODO: fix word count!!! Eg. simple-example/index shows 62 when in MS Word it's 87.
    return len(soup_contents), len(words)


def _make_fwarning_dropdown(msg: FileVerificationMessageJson) -> str:
    directive, grid, grid_item = r"{dropdown}", r"{grid}", r"{grid-item}"
    return f""" \n
:::::{directive} {msg["problem"]}
**{msg["problem"]}** {msg["recommend"]}
::::{grid}
:::{grid_item}
:columns: 1
:::
:::{grid_item}
:columns: 11
{msg["prev_elem"]}
:::
:::{grid_item}
:columns: 1
👉
:::
:::{grid_item}
:columns: 11
{msg["curr_elem"]}
:::
:::{grid_item}
:columns: 1
:::
:::{grid_item}
:columns: 11
{msg["next_elem"]}
:::
::::
:::::
\n"""
