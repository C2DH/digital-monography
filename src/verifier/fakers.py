import pathlib
import typing as t

try:
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath


class Faker:
    def __new__(cls, service_name: str) -> None:
        fakers = [
            ("s3", S3Faker),
            ("sqs", SQSFaker),
        ]
        for faker in fakers:
            if service_name == faker[0]:
                return super().__new__(faker[1])
        raise NotImplementedError


class S3Faker:

    def download_fileobj(
        self, Bucket, Key, Fileobj, ExtraArgs=None, Callback=None, Config=None
    ):
        """
        In boto3, download_fileobj has to download an object from S3 to a
        file-like object in the shared file system (/mnt/efs/...).
        In the faker, it just copies the object data/input/... source to the
        /tmp/efs/_INPUT dir (or wherever target was defined in constants.py).
        """
        source_fp = pathlib.Path("/tmp") / "efs" / "_INPUT"
        key = KeyPath(Key)
        for keypart in key.parts:
            source_fp = source_fp / keypart
        with open(source_fp, mode="rb") as source_file:
            Fileobj.write(source_file.read())

    def put_object(self, Body: bytes, Bucket: str, Key: str):
        """
        In boto3, put_object adds an object to a bucket. Here it copies
        the file to /tmp/efs/<bucket_name> and returns a fake response.
        """
        target_fp = pathlib.Path("/tmp") / "efs" / Bucket
        for key_part in pathlib.Path(Key).parts:
            target_fp = target_fp / key_part
        target_fp.parent.mkdir(parents=True, exist_ok=True)
        with open(target_fp, mode="w") as f:
            f.write(Body)
        return {
            "ResponseMetadata": {
                "RequestId": "ABCDEFGHIJKLMNOP",
                "HostId": "WVRUDD8aiLUYuWkG+ebcP88QcdpSBd/a+XkRLIskiti1qz9ZSYlXEyDQkjW6z7KVd6F5coE/kJA=",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amz-id-2": "WVRUDD8aiLUYuWkG+ebcP88QcdpSBd/a+XkRLIskiti1qz9ZSYlXEyDQkjW6z7KVd6F5coE/kJA=",
                    "x-amz-request-id": "ABCDEFGHIJKLMNOP",
                    "date": "Fri, 01 Jun 2024 01:01:01 GMT",
                    "x-amz-server-side-encryption": "AES256",
                    "etag": '"just-uuid-id"',
                    "server": "AmazonS3",
                    "content-length": "0",
                },
                "RetryAttempts": 0,
            },
            "ETag": '"just-uuid-id"',
            "ServerSideEncryption": "AES256",
        }


class SQSFaker:
    def send_message(
        self,
        QueueUrl: str,
        MessageBody: str,
        MessageDeduplicationId: str,
        MessageGroupId: str,
    ) -> dict[str, t.Union[str, int]]:
        return {
            "MD5OfMessageBody": "201ae3116cba610bc56a93c227353227",
            "MessageId": "c0712d34-7bb0-409c-9e3c-3ccfe4764d82",
            "SequenceNumber": "18887419945533167872",
            "ResponseMetadata": {
                "RequestId": "125e768e-187c-5b93-972c-299a4e1073e8",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amzn-requestid": "125e768e-187c-5b93-972c-299a4e1073e8",
                    "date": "Fri, 01 Jun 2024 01:01:01 GMT",
                    "content-type": "application/x-amz-json-1.0",
                    "content-length": "146",
                    "connection": "keep-alive",
                },
                "RetryAttempts": 0,
            },
        }
