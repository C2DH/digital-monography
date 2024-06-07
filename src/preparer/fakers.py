import pathlib

try:
    from .keys import KeyPath
except Exception as e:
    from keys import KeyPath


class Faker:
    def __new__(cls, service_name: str) -> None:
        fakers = [
            ("s3", S3Faker),
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
        /tmp/efs/... target (or wherever target was defined in constants.py).
        """
        source_fp = pathlib.Path("/tmp") / "dgtmon_input"
        key = KeyPath(Key)
        for keypart in key.parts:
            source_fp = source_fp / keypart
        with open(source_fp, mode="rb") as source_file:
            Fileobj.write(source_file.read())

    def put_object(self, Body: bytes, Bucket: str, Key: str):
        """
        In boto3, put_object adds an object to a bucket.
        Here it just returns the same response.
        """
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
