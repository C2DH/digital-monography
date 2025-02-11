import argparse
import base64
import bs4
import datetime
import docx
import io
import mammoth
import pathlib
from PIL import Image
import uuid

from constants import (
    MAMMOTH_STYLE_MAP,
    METADATA_FIELDS,
    FIELD_DIGITAL_SOURCE,
    FIELD_PAPER_SOURCE,
)


parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path")


if __name__ == "__main__":
    args = parser.parse_args()
    book_path_arg = args.book_path.split("=")
    assert len(book_path_arg) == 2
    book_path = pathlib.Path(book_path_arg[1])
    metadata_tables = {}

    digital_input_field = next(
        f for f in METADATA_FIELDS if f["key"] == FIELD_DIGITAL_SOURCE
    )
    paper_input_field = next(
        f for f in METADATA_FIELDS if f["key"] == FIELD_PAPER_SOURCE
    )
    iscolor_field = next(f for f in METADATA_FIELDS if f["key"] == "iscolor")
    metadata_descs = {}
    for field in METADATA_FIELDS:
        metadata_descs[field["show"]] = field["desc"]

    assert book_path.exists(), f"{book_path} does not exist"
    (book_path / "assets").mkdir(exist_ok=True)
    for fp in book_path.glob("*"):
        if not fp.exists() or fp.is_dir():
            continue
        elif fp.name.startswith("~$"):
            continue
        elif fp.suffix == ".docx":
            metadata_tables[fp.name] = []
            with open(fp, "rb") as f:
                target_dir = book_path / "assets" / fp.stem
                target_dir.mkdir(exist_ok=True)
                result = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
                html_str = result.value
                html_soup = bs4.BeautifulSoup(html_str, "html.parser")
                imgs = html_soup.find_all("img")

                for i, img in enumerate(imgs, start=1):

                    if i > 5:
                        break

                    img_metadata = {}
                    img: bs4.element.Tag
                    src: str = img["src"]
                    alttext: str = img.get("alt", "")
                    start = src.index("/") + 1
                    end = src.index(";", start)
                    suffix = src[start:end]
                    encodded_img = src.split(",")[-1]
                    assert target_dir.exists(), f"{target_dir} does not exist"
                    fn = "{i:03}.{suffix}".format(i=i, suffix=suffix)
                    pil_img = Image.open(io.BytesIO(base64.b64decode(encodded_img)))
                    pil_img.save(target_dir / fn, quality=100, subsampling=0)
                    print(f"saved {(target_dir / fn)}")

                    # 4. make a metadata dump for each image
                    for field in METADATA_FIELDS:
                        img_metadata["img"] = encodded_img
                        if field["is_required"] and field["key"] == "id":
                            img_metadata[field["show"]] = uuid.uuid4().hex
                        elif field["is_required"] and field["key"] == "alttext":
                            img_metadata[field["show"]] = alttext
                        elif field["is_required"] and field["key"] in (
                            FIELD_DIGITAL_SOURCE,
                            FIELD_PAPER_SOURCE,
                        ):
                            input_target = "/".join((target_dir / fn).parts[-3:])
                            img_metadata[digital_input_field["show"]] = input_target
                            img_metadata[paper_input_field["show"]] = input_target
                        elif field["is_required"]:
                            img_metadata[field["show"]] = ""
                    img_metadata[iscolor_field["show"]] = ""
                    metadata_tables[fp.name].append(img_metadata)

    # 5. save metadata dump to docx
    doc = docx.Document()
    doc.add_heading("Figures metadata", level=1)
    for docx_fp, tables_data in metadata_tables.items():
        doc.add_heading(docx_fp, level=2)
        for table_data in tables_data:
            table_data: dict
            _img = table_data.pop("img")
            doc.add_picture(
                io.BytesIO(base64.b64decode(_img)), width=docx.shared.Inches(2)
            )
            tbl = doc.add_table(len(table_data), cols=2, style="Table Grid")
            for i, (key, value) in enumerate(table_data.items()):
                tbl.cell(i, 0).text = key
                tbl.cell(i, 1).text = value

            doc.add_paragraph("")
            doc.add_paragraph("Meaning of the fields:")
            for field_name in table_data.keys():
                doc.add_paragraph(
                    field_name + " - " + metadata_descs[field_name], style="List Bullet"
                )
            doc.add_page_break()

    doc.save(
        book_path
        / "assets"
        / f"{datetime.date.today().isoformat()}_editorial_notes.docx"
    )

    print("end")
