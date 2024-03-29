import boto3
import os
import pathlib
import time

try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False

STATICWS_WIP_BUCKET_NAME = "dgtmon-dev-staticws-wip"
IR_APKG_HTML_BUCKET_NAME = "dgtmon-dev-ir-apkg-html"
IR_APKG_MD_BUCKET_NAME = "dgtmon-dev-ir-apkg-md"
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
        cls.s3 = get_aws_client("s3")
        cls.slug = "my-book"
        # trigger s3 event
        fp = pathlib.Path("tests") / "_fixtures" / "footnote-hyperlink.docx"
        key = fp.name  # f"{cls.slug}/{fp.name}"
        with fp.open(mode="rb") as fileobj:
            cls.s3.upload_fileobj(fileobj, UPLOAD_APKG_BUCKET_NAME, fp.name)
        # cls.s3.put_object(
        #     Bucket=UPLOAD_APKG_BUCKET_NAME,
        #     Key="index.html",
        #     Body=fp.read_bytes(),
        # )

    def test_if_object_was_uploaded_to_irapkghtml_bucket(self):
        loop = 0
        expected_html = (
            '<p><sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup></p>'
            + '<ol><li id="footnote-1"><p> <a href="http://www.example.com">Example</a> <a href="#footnote-ref-1">↑</a></p></li></ol>'
        )
        while True:
            try:
                key = f"footnote-hyperlink.html"
                resp = self.s3.get_object(Bucket=IR_APKG_HTML_BUCKET_NAME, Key=key)
                contents = resp["Body"].read().decode("utf-8")
                if contents.startswith(expected_html):
                    break
                if loop > 20:
                    break
            except:
                pass
            loop += 1
            time.sleep(0.5)
        assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert contents.startswith(expected_html)

    def test_if_object_was_uploaded_to_irapkgmd_bucket(self):
        loop = 0
        expected_md = "[^footnote-ref-1]\n\n[^http://www.example.com]: Example\n"
        while True:
            try:
                key = f"footnote-hyperlink.md"
                resp = self.s3.get_object(Bucket=IR_APKG_MD_BUCKET_NAME, Key=key)
                contents = resp["Body"].read().decode("utf-8")
                if contents.startswith(expected_md):
                    break
                if loop > 20:
                    break
            except:
                pass
            loop += 1
            time.sleep(0.5)
        assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert contents.startswith(expected_md)

    # def test_if_object_was_uploaded_to_staticwswip_bucket(self):
    #     loop = 0
    #     expected_val = "<!DOCTYPE html><html><head><title>Testing"
    #     while True:
    #         try:
    #             resp = self.s3.get_object(
    #                 Bucket=STATICWS_WIP_BUCKET_NAME, Key="footnote-hyperlink.html"
    #             )
    #             contents = resp["Body"].read().decode("utf-8")
    #             if contents.startswith(expected_val):
    #                 break
    #             if loop > 20:
    #                 break
    #         except:
    #             pass
    #         loop += 1
    #         time.sleep(0.5)
    #     print(contents)
    #     assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
    #     assert contents.startswith(expected_val)

    @classmethod
    def teardown_class(cls):
        pass


# aws logs get-log-events --endpoint-url=http://localhost:4566 --log-group-name /aws/lambda/builder --log-stream-name XXX
