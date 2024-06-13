import argparse
import copy
import pathlib
import shutil
import sys
import os

# Get the parent directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.preparer.main import lambda_handler as preparer_handler
from src.builder.main import lambda_handler as builder_handler
from scripts.sync import listen_for_updates

parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path")


DEFAULT_EVENT = {
    "Records": [
        {
            "eventVersion": "2.1",
            "eventSource": "aws:s3",
            "awsRegion": "eu-west-1",
            "eventTime": "2024-06-01T10:01:01.100Z",
            "eventName": "ObjectCreated:Put",
            "userIdentity": {"principalId": "AWS:AROAVK5GEQE3275W6UTUO:preparer"},
            "requestParameters": {"sourceIPAddress": "10.10.2.149"},
            "responseElements": {
                "x-amz-request-id": "7MMJ7WJPN7GM5KYN",
                "x-amz-id-2": "E3m/Eudcp6Z7vZh9Ex1blHs1bHy7ajDl71V6BBnXFD5dwiHqE+ylOE578E4+ShRpve8ctI5y9abpl4QbtsPrl3XhN8bxbgiF",
            },
            "s3": {
                "s3SchemaVersion": "1.0",
                "configurationId": "tf-s3-lambda-20240531090332003100000001",
                "bucket": {
                    "name": "dgtmon-dev-apkg-upload",
                    "ownerIdentity": {"principalId": "A13XBETHGUR4IG"},
                    "arn": "arn:aws:s3:::dgtmon-dev-apkg-upload",
                },
                "object": {
                    "key": "PLACE YOUR SLUG/PATH/TO/FILE HERE",
                    "size": 278,
                    "eTag": "3647c11ea643861bb23a8dd628cd0642",
                    "sequencer": "00665DF6D32A167391",
                },
            },
        }
    ]
}


def cpy_to_tmp_and_call_handler(fp: pathlib.Path, key: str):
    target_fp = pathlib.Path("/tmp") / "efs" / "_INPUT"
    for key_part in pathlib.Path(key).parts:
        target_fp = target_fp / key_part
    target_fp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fp, target_fp)
    event = copy.deepcopy(DEFAULT_EVENT)
    event["Records"][0]["s3"]["object"]["key"] = key
    context = {}
    # lambda handlers
    preparer_handler(event, context)
    builder_handler(event, context)


if __name__ == "__main__":
    args = parser.parse_args()
    book_path_arg = args.book_path.split("=")
    assert len(book_path_arg) == 2
    book_path = pathlib.Path(book_path_arg[1])
    listen_for_updates(book_path, cpy_to_tmp_and_call_handler)
