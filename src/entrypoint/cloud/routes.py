import flask
import json
import logging
import os

from .aws import s3_list_objects, dynamodb_client


cloud_bp = flask.Blueprint("cloud", __name__)


"""
This blueprint handles all cloud-related API endpoints, i.e.
fetching data from s3 object storage and dynamodb database.
"""


@cloud_bp.route("/list-warnings", methods=["GET"])
def list_warnings() -> flask.Response:
    """List objects in a warnings bucket."""
    logging.info("List warnings REST api endpoint was called with GET.")
    slug = flask.request.args.get("slug")
    contents = s3_list_objects(os.environ.get("VERIFIER_MSGS", ""), f"{slug}/")
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/list-assets", methods=["GET"])
def list_assets_from_s3() -> flask.Response:
    """List objects in a upload slug/assets/* bucket."""
    logging.info("List assets REST api endpoint was called with GET.")
    slug = flask.request.args.get("slug")
    bucket = os.environ.get("APKG_UPLOAD_BUCKET_NAME", "")
    contents = s3_list_objects(bucket, prefix=f"{slug}/assets/")
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/assets", methods=["GET"])
def list_assets_from_dynamodb() -> flask.Response:
    """Retrieve assets from the database and return them to the client."""
    logging.info("Retrieve assets from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb_client.query(
        TableName=os.environ.get("DYNAMODB_ASSETS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/refs", methods=["GET"])
def list_refs_from_dynamodb() -> flask.Response:
    """Retrieve refs from the database and return them to the client."""
    logging.info("Retrieve refs from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb_client.query(
        TableName=os.environ.get("DYNAMODB_REFS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/events", methods=["GET"])
def query_events() -> flask.Response:
    """Retrieve events from the database and return them to the client."""
    logging.info("Retrieve events from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb_client.query(
        TableName=os.environ.get("DYNAMODB_AUDIT_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/alerts", methods=["GET"])
def query_alerts() -> flask.Response:
    """Retrieve alerts from the database and return them to the client."""
    logging.info("Retrieve alerts from the database and return them to the client.")
    resp = dynamodb_client.scan(
        TableName=os.environ.get("DYNAMODB_ALERTS_TBL", ""),
    )
    contents = resp["Items"]
    logging.info(f"Resp: {json.dumps(resp, default=str)}")
    while "LastEvaluatedKey" in resp:
        resp = dynamodb_client.scan(
            TableName=os.environ.get("DYNAMODB_ALERTS_TBL", ""),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        logging.info(f"Resp: {json.dumps(resp, default=str)}")
        contents.extend(resp["Items"])
    logging.info(f"Contents: {json.dumps(contents, default=str)}")
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/citations", methods=["GET"])
def query_citations() -> flask.Response:
    """Retrieve citations from the database and return them to the client."""
    logging.info("Retrieve citations from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb_client.query(
        TableName=os.environ.get("DYNAMODB_CITATIONS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@cloud_bp.route("/headings", methods=["GET"])
def query_headings() -> flask.Response:
    """Retrieve headings from the database and return them to the client."""
    logging.info("Retrieve headings from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb_client.query(
        TableName=os.environ.get("DYNAMODB_HEADINGS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp
