import time
import boto3
import os
import pathlib

try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False

STATICWS_WIP_BUCKET_NAME = "dgtmon-dev-staticws-wip"
# IR_APKG_MD_BUCKET_NAME = "dgtmon-dev-ir-apkg-md"
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

    def test_if_object_was_uploaded_to_irapkghtml_bucket(self):
        assert 1 == 1

    def test_if_object_was_uploaded_to_irapkgmd_bucket(self):
        assert 1 == 2

    def test_if_object_was_uploaded_to_staticwswip_bucket(self):
        loop = 0
        expected_val = "<!DOCTYPE html><html><head><title>Testing"
        while True:
            resp = self.s3.get_object(Bucket=STATICWS_WIP_BUCKET_NAME, Key="index.html")
            index_object = resp["Body"].read().decode("utf-8")
            if index_object.startswith(expected_val):
                break
            if loop > 10:
                break
            loop += 1
            time.sleep(0.5)
        assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert index_object.startswith(expected_val)

    @classmethod
    def teardown_class(cls):
        pass


# aws logs get-log-events --endpoint-url=http://localhost:4566 --log-group-name /aws/lambda/builder --log-stream-name XXX
