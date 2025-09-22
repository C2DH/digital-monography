import argparse
import copy
import pathlib
import shutil
import sys
import os
import time


os.environ["DGTMON_DEBUG"] = "1"


# Get the parent directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src._common.keys import KeyPath
from src.preparer.main import lambda_handler as preparer_handler
from src.builderv3.main import lambda_handler as builder_handler
from src.verifier.main import lambda_handler as verifier_handler
from src.wordprocessor.main import lambda_handler as wordprocessor_handler
from scripts.sync import listen_for_updates

parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path")
parser.add_argument("--skip-build", action="store_true")
# parser.add_argument("--wait", action="store_true")


DEFAULT_S3_EVENT = {
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
DEFAULT_SQS_EVENT = {
    "Records": [
        {
            "messageId": "05e84d45-cf03-4736-b4f6-cfeb224a3c28",
            "receiptHandle": "AQEBnn8NI0PqDy2vnE+zIr9zMt8EZtxJsNP8EoE518jUB5kM9XfxBISr0y5x/1rLJ5Q8H7ZC8Ki1L4kFqxoDcLrQhaWtYVd3UgGc+QQqiSROweMQbf9HO/UC1AtJwhvxrXqwLJOlwdDMQDqUNVreEw+r49ImzFHeA2PVnCpWlGUxxywJb5PK5aln3taoF9gFF+dYHeY20kCT9FvwcZ/8FPEfWtR0WbTjmK0SGjRC6zNTppLeYmNsWK8WlJuyKssAUDH31swhOM/lCpUFoclUnApDBgUmW1aTW9xxqhnNyV9zVFAz72dwBxxk8ZYomdV1+6LT",
            "body": "PLACE YOUR SLUG HERE",
            "attributes": {
                "ApproximateReceiveCount": "1",
                "AWSTraceHeader": "Root=1-669541a5-07b9fdc04aa5c7df7bdc7bf6;Parent=3f6868ca47622a17;Sampled=0;Lineage=d722ee3a:0",
                "SentTimestamp": "1721057704521",
                "SequenceNumber": "18887334846066927616",
                "MessageGroupId": "0",
                "SenderId": "AROAVK5GEQE3275W6UTUO:preparer",
                "MessageDeduplicationId": "PLACE YOUR SLUG HERE",
                "ApproximateFirstReceiveTimestamp": "1721057709530",
            },
            "messageAttributes": {},
            "md5OfBody": "201ae3116cba610bc56a93c227353227",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:eu-west-1:367031255351:cpy-dgtmon-dev-builder-trigger.fifo",
            "awsRegion": "eu-west-1",
        }
    ]
}


def cpy_to_tmp_and_call_handler(fp: pathlib.Path, key: str) -> dict[str, float]:
    time_status = {}
    target_fp = pathlib.Path("/tmp") / "efs" / "_INPUT"
    for key_part in pathlib.Path(key).parts:
        target_fp = target_fp / key_part
    target_fp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fp, target_fp)
    s3_event = copy.deepcopy(DEFAULT_S3_EVENT)
    s3_event["Records"][0]["s3"]["object"]["key"] = key
    context = {}
    # preparer
    start = time.time()  # consider time.perf_counter or time.process_time
    preparer_handler(s3_event, context)
    time_status["preparer"] = time.time() - start
    # verifier
    if key.endswith(".docx"):
        start = time.time()  # consider time.perf_counter or time.process_time
        s3_event["Records"][0]["s3"]["object"]["key"] = str(
            KeyPath(key).with_suffix(".html")
        )
        verifier_handler(s3_event, context)
        time_status["verifier"] = time.time() - start
    return time_status


def build_after_loop(book_path: pathlib.Path) -> dict[str, float]:
    # builder
    start = time.time()  # consider time.perf_counter or time.process_time
    slug = book_path.parts[-1]
    context = {}
    sqs_event = copy.deepcopy(DEFAULT_SQS_EVENT)
    sqs_event["Records"][0]["body"] = slug
    sqs_event["Records"][0]["attributes"]["MessageDeduplicationId"] = slug
    wordprocessor_handler(sqs_event, context)
    builder_handler(sqs_event, context)
    end = time.time()
    return {"builder": end - start}


if __name__ == "__main__":
    args = parser.parse_args()
    book_path_arg = args.book_path.split("=")
    assert len(book_path_arg) == 2
    book_path = pathlib.Path(book_path_arg[1])
    if args.skip_build:
        listen_for_updates(book_path, cpy_to_tmp_and_call_handler)
    else:
        listen_for_updates(book_path, cpy_to_tmp_and_call_handler, build_after_loop)
    # If DGTMON_VOLUME is not set, listen_for_updates() waits for updates,
    # so nothing can be processed afterwards.
