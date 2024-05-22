import pathlib
import time
import boto3

BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/thinkering-with-memorecord"
BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/guidelines-for-drafting-manuscripts"
DST = "cpy-dgtmon-dev-apkg-upload"  # TODO: read from .tfvars


s3 = boto3.client("s3")

if __name__ == "__main__":
    last_modified = {}
    book_path = pathlib.Path(BOOK_PATH)
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
                with fp.open(mode="rb") as fileobj:
                    resp = s3.upload_fileobj(fileobj, DST, key)
                last_modified[fp] = fp.stat().st_mtime
                print(f"Uploaded {key}.")
            time.sleep(0.1)
            print("...")
