import boto3
import os
import pathlib

try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False

STATICWS_WIP_BUCKET_NAME = "dgtmon-dev-staticws-wip"
UPLOAD_APKG_BUCKET_NAME = "dgtmon-dev-apkg-upload"


def get_aws_client(service: str):
    if IS_LOCAL:
        return boto3.client(
            service,
            aws_access_key_id="",
            aws_secret_access_key="",
            region_name="eu-central-1",
            endpoint_url="http://localhost:4566",
        )
    else:
        return boto3.client(service)


class TestClass:
    @classmethod
    def setup_class(cls):
        cls.logs = get_aws_client("logs")
        cls.s3 = get_aws_client("s3")
        # trigger s3 event
        fp = pathlib.Path("tests") / "_fixtures" / "new_object.html"
        cls.s3.put_object(
            Bucket=UPLOAD_APKG_BUCKET_NAME,
            Key="index.html",
            Body=fp.read_bytes(),
        )

    def test_s3_upload(self):
        resp = self.s3.get_object(Bucket=STATICWS_WIP_BUCKET_NAME, Key="index.html")
        index_object = resp["Body"].read().decode("utf-8")
        assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert index_object.startswith("<!DOCTYPE html><html><head><title>Testing")

    @classmethod
    def teardown_class(cls):
        pass


# aws logs get-log-events --endpoint-url=http://localhost:4566 --log-group-name /aws/lambda/builder --log-stream-name XXX
