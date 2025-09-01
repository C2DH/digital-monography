import base64
import boto3
import datetime
import logging
import json
import os
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)
from mypy_boto3_secretsmanager.client import (
    SecretsManagerClient as boto3_SecretsManagerClient,
)
from mypy_boto3_sqs import SQSClient as boto3_SQSClient


dynamodb_res: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")
secretsmanager: boto3_SecretsManagerClient = boto3.client("secretsmanager")
sqs: boto3_SQSClient = boto3.client("sqs")


def dynamodb_set(tbl: str, **kwargs) -> None:
    logging.info(
        f"Setting item in DynamoDB table {tbl} with attributes: {json.dumps(kwargs)}"
    )
    expire_at = int((datetime.datetime.now() + datetime.timedelta(days=3)).timestamp())
    table = dynamodb_res.Table(tbl)
    logging.info(f"dynamodb_res.Table: {table}")
    resp = table.put_item(Item={"expire_at": expire_at, **kwargs})
    logging.info(
        f"Response from dynamodb.Table({tbl}).put_item: {json.dumps(resp, default=str)}"
    )


def send_msg_to_sqs(request_data: bytes) -> None:
    try:
        QueueUrl = os.environ.get("SQS_URL", "")
        MessageBody = base64.b64encode(request_data).decode("utf-8")
        resp = sqs.send_message(
            QueueUrl=QueueUrl,
            MessageBody=MessageBody,
        )
        logging.info(
            f"Response from sqs.send_message(QueueUrl={QueueUrl}, MessageBody={MessageBody}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logging.exception(f"Sending a message to sqs queue failed. Error: {repr(e)}")
        raise
