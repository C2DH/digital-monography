import bs4
import logging
import typing as t


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:

    return {"statusCode": 200, "body": ""}
