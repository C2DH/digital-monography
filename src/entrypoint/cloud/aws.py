import boto3
import typing as t
from mypy_boto3_dynamodb.client import DynamoDBClient as boto3_DynamoDBClient
from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_s3.type_defs import ObjectTypeDef as boto3_ObjectTypeDef


s3: boto3_S3Client = boto3.client("s3")
dynamodb_client: boto3_DynamoDBClient = boto3.client("dynamodb")


def s3_list_objects(bucket: str, prefix: t.Optional[str]) -> list[boto3_ObjectTypeDef]:
    if prefix:
        # objects = s3.list_objects_v2(Bucket=bucket, Prefix=f"{slug}/")
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    else:
        objects = s3.list_objects_v2(Bucket=bucket)
    if "Contents" in objects:
        return objects["Contents"]
    else:
        return []
