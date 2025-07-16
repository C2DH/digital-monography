import boto3
import pathlib
import os
import time
import typing as t

BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/thinkering-with-memorecord"
BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/guidelines-for-drafting-manuscripts"
BOOK_PATH = (
    "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/examples"
)
BOOK_PATH = "/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/small-example"
DST = "cpy-dgtmon-dev-apkg-upload"  # TODO: read from .tfvars


s3 = boto3.client("s3")


def listen_for_updates(
    book_path: pathlib.Path,
    func_on_update: t.Callable,
    func_after_loop: t.Optional[t.Callable] = None,
) -> None:
    last_modified = {}
    is_update = False
    while True:
        time_status = {}
        for fp in book_path.glob("**/*"):
            if not fp.exists() or fp.is_dir():
                is_update = False
                continue
            if fp.name.startswith("~$"):
                is_update = False
                continue
            if fp not in last_modified:
                last_modified[fp] = 0
            if fp.stat().st_mtime > last_modified[fp]:
                is_update = True
                key = str(fp.relative_to(book_path.parent))
                time_status.update(func_on_update(fp, key))
                last_modified[fp] = fp.stat().st_mtime
                print(f"Uploaded {key}.")
        if is_update and func_after_loop is not None:
            time_status.update(func_after_loop(book_path))
        if os.environ.get("DGTMON_VOLUME") is not None:
            total_t = sum(time_status.values())
            for k, v in time_status.items():
                print(f"{k}: {v} sec ({(v / total_t) * 100}%)")
            print("-" * 50)
            print(f"total: {total_t} (100%)")
            break
        if os.environ.get("DGTMON_NO_WAIT") is not None:
            if not is_update:
                time_status.update(func_after_loop(book_path))
            break
        else:
            print(".", end="", flush=True)
            time.sleep(0.1)


if __name__ == "__main__":
    book_path = pathlib.Path(BOOK_PATH)

    def upload_to_s3(fp: pathlib.Path, key: str):
        with fp.open(mode="rb") as fileobj:
            s3.upload_fileobj(fileobj, DST, key)

    # func_after_loop is used in `prepare_and_build.py` script
    # to run the builder lambda_handler only after a loop.
    func_after_loop = None

    listen_for_updates(book_path, upload_to_s3, func_after_loop)
