import boto3
import pathlib
import time
import typing as t

BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/thinkering-with-memorecord"
BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/guidelines-for-drafting-manuscripts"
BOOK_PATH = (
    "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/examples"
)
DST = "cpy-dgtmon-dev-apkg-upload"  # TODO: read from .tfvars


s3 = boto3.client("s3")


def listen_for_updates(book_path: pathlib.Path, func_on_update: t.Callable) -> None:
    last_modified = {}
    while True:
        for fp in book_path.glob("**/*"):
            if not fp.exists() or fp.is_dir():
                continue
            if fp.name.startswith("~$"):
                continue
            if fp not in last_modified:
                last_modified[fp] = 0
            if fp.stat().st_mtime > last_modified[fp]:
                key = str(fp.relative_to(book_path.parent))
                func_on_update(fp, key)
                last_modified[fp] = fp.stat().st_mtime
                print(f"Uploaded {key}.")
            time.sleep(0.1)
            print("...")


if __name__ == "__main__":
    book_path = pathlib.Path(BOOK_PATH)

    def upload_to_s3(fp: pathlib.Path, key: str):
        with fp.open(mode="rb") as fileobj:
            resp = s3.upload_fileobj(fileobj, DST, key)

    listen_for_updates(book_path, upload_to_s3)
