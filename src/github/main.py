import base64
import json
import boto3
import logging
import requests
import typing as t
import urllib.parse

try:
    from constants import (
        ARCHIVE_APKG_ALL,
        GITHUB_ORG,
        GITHUB_TOKEN,  # TODO: fetch from AWS Secrets Manager
    )
    from keys import KeyPath
except ModuleNotFoundError as e:
    from src.github.constants import (
        ARCHIVE_APKG_ALL,
        GITHUB_ORG,
        GITHUB_TOKEN,  # TODO: fetch from AWS Secrets Manager
    )
    from src.github.keys import KeyPath


logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.client("s3")
secretsmanager = boto3.client("secretsmanager")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Starting GitHub Lambda.")
    logger.info(json.dumps(event, default=str))
    logger.info(json.dumps(context, default=str))

    try:
        logger.info("Pre get_secret_value")
        resp = secretsmanager.get_secret_value(SecretId="dgtmon-dev-github-api-token")
        logger.info("Post get_secret_value")
        logger.info(
            "secretsmanager.get_secret_value response: " + json.dumps(resp, default=str)
        )
        api_key = resp["SecretString"]
        logger.info("api_key" + api_key)
    except Exception as e:
        logging.exception(f"Error while getting secret value: {repr(e)}")
        raise

    return {"statusCode": 200, "body": ""}
    # naively try to create without checking if the repo exists
    key = _get_key(event)
    logger.info("Key: " + str(key))
    logger.info("Key.efs_filepath: " + str(key.efs_filepath))

    ###
    # does not work, [Errno 2] No such file or directory: '/tmp/examples/_config.yml'
    # with open(key.efs_filepath, "r") as f:
    #     contents = f.read()
    # logger.info("Contents: " + contents)
    ###

    _create_github_repo(key)
    new_bytes = _get_obj_from_archive_s3(key)
    prev_obj = _get_from_github_repo(key)
    prev_v_sha = prev_obj.json().get("sha", None)
    _put_to_github_repo(key, new_bytes, prev_v_sha, event, context)
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        return KeyPath(key_str)
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _create_github_repo(key: KeyPath) -> requests.Response:
    """
    Creates a new repository in the specified organization.
    Note that the GitHub API token must have the write "Administration" repo permissions.
    If the repository already exists, the repository creation will fail with a message
    "name already exists on this account".
    See API docs here:
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-an-organization-repository
    """
    data = {
        "name": key.slug,
        # "description": "",  # TODO: get a desc from `key.efs_slug_dir / "_config.yml"`
        # "homepage": "",  # TODO: link to the digital version of the book
        "private": False,
        "visibility": "public",
        "security_and_analysis": None,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
        "is_template": False,
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        res = requests.post(
            f"https://api.github.com/orgs/{GITHUB_ORG}/repos",
            json=data,
            headers=headers,
        )
        logger.info(json.dumps(res.json(), default=str))
        return res
    except Exception as e:
        logging.exception(
            f"Error while sending request to update github repo: {repr(e)}"
        )
        raise


def _get_obj_from_archive_s3(key: KeyPath) -> bytes:
    try:
        resp = s3.get_object(
            Bucket=ARCHIVE_APKG_ALL,
            Key=str(key.s3_key),
        )
        logger.info(
            f"Response from s3.get_object(Bucket={ARCHIVE_APKG_ALL}, Key={key.s3_key}): "
            + json.dumps(resp, default=str)
        )
        contents = resp["Body"].read()
        logger.info(f"Retrieved object as str: " + contents.decode("utf-8"))
        return contents
    except Exception as e:
        logging.exception(f"Error while getting object from s3: {repr(e)}")
        raise


def _get_from_github_repo(key: KeyPath) -> requests.Response:
    """
    Gets the contents of a file in a repository.
    See API docs here:
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
    """
    try:
        res = requests.get(
            f"https://api.github.com/repos/{GITHUB_ORG}/{key.slug}/contents/{key.github_path}",
        )
        logger.info(json.dumps(res.json(), default=str))
        return res
    except Exception as e:
        logger.error(
            f"Unable to retrieve the previous version of the {key.s3_key} file. Error: {repr(e)}"
        )
        raise


def _put_to_github_repo(
    key: KeyPath, contents: bytes, prev_v_sha: t.Optional[str], event, context
) -> requests.Response:
    """
    Creates a new file or replaces an existing file in a repository.
    See API docs here:
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents
    """
    b64content = base64.b64encode(contents).decode()
    try:
        eventSource = event["Records"][0]["eventSource"]
        eventName = event["Records"][0]["eventName"]
        eventTime = event["Records"][0]["eventTime"]
        requestId = event["Records"][0]["responseElements"]["x-amz-request-id"]
    except Exception as e:
        logger.error(f"Unable to retrieve the event data. Error: {repr(e)}")
        raise
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "message": f"{eventTime} [{requestId}] Perform action {eventSource}:{eventName} on '{key.s3_key}'",
        "content": b64content,
        # "committer": { # TODO: figure out how to extract data of the commiter & author
        #     "name": "",
        #     "email": "",
        # },
        # "author": {
        #     "name": "",
        #     "email": "",
        # },
    }
    if prev_v_sha:
        data.update({"sha": prev_v_sha})
    try:
        res = requests.put(
            f"https://api.github.com/repos/{GITHUB_ORG}/{key.slug}/contents/{key.github_path}",
            json=data,
            headers=headers,
        )
        logger.info(json.dumps(res.json(), default=str))
        return res
    except Exception as e:
        logging.exception(
            f"Error while sending request to update github repo: {repr(e)}"
        )
        raise
