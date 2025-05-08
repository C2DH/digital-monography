import base64
import boto3
import datetime
import json
import logging
import os
import requests
import typing as t
import urllib.parse

try:
    from audit import AuditEvent, AuditStatus
    from constants import (
        ModuleEnum,
        APKG_UPLOAD_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        GITHUB_SECRET_ID,
    )
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .audit import AuditEvent, AuditStatus
    from .constants import (
        ModuleEnum,
        APKG_UPLOAD_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        GITHUB_SECRET_ID,
    )
    from .keys import KeyPath


logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.client("s3")
secretsmanager = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")


class GitHubSecret(t.TypedDict):
    github_api_token: str
    github_api_org: str
    # as a hack I added third field to be used by another module


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Starting GitHub Lambda.")
    logger.info(json.dumps(event, default=str))
    logger.info(json.dumps(context, default=str))

    key = _get_key(event)
    # if key.suffix not in [".md", ".MD", ".ipynb", ".IPYNB"]:
    #     return {"statusCode": 200, "body": ""}

    secret = _get_api_key(key, os.environ.get("GITHUB_SECRET_ID", ""))

    # naively try to create repo without checking if it exists
    _create_github_repo(key, secret)
    new_bytes = _get_obj_from_s3(key)
    prev_obj = _get_from_github_repo(key, secret)
    prev_v_sha = prev_obj.json().get("sha", None)
    _put_to_github_repo(key, secret, new_bytes, prev_v_sha, event)
    _log_audit_event(
        key,
        AuditStatus.SUCCESS.value,
        "Changes saved to GitHub repository.",
    )
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["body"], encoding="utf-8"
        )
        return KeyPath(key_str)
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _get_api_key(key: KeyPath, secret_id: str) -> GitHubSecret:
    try:
        resp = secretsmanager.get_secret_value(SecretId=secret_id)
        return json.loads(resp["SecretString"])
    except Exception as e:
        logging.exception(
            f"Error while getting secret value for {secret_id}: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal authentication.",
        )
        raise


def _create_github_repo(key: KeyPath, secret: GitHubSecret) -> requests.Response:
    """
    Creates a new repository in the specified organization.
    Note that the GitHub API token must have the write "Administration" repo permissions.
    If the repository already exists, the repository creation will fail with a message
    "name already exists on this account".
    See API docs here:
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-an-organization-repository
    """
    try:
        github_token = secret["github_api_token"]
        github_org = secret["github_api_org"]
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
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        res = requests.post(
            f"https://api.github.com/orgs/{github_org}/repos",
            json=data,
            headers=headers,
        )
        logger.info(json.dumps(res.json(), default=str))
        if res.ok:
            first_readme = b'# Welcome to the publication\nTo start or join a conversation, go to the "Issues" section.'
            b64content = base64.b64encode(first_readme).decode()
            github_token = secret["github_api_token"]
            github_org = secret["github_api_org"]
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {github_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            data = {
                "message": f"Add README.md",
                "content": b64content,
            }
            readme_response = requests.put(
                f"https://api.github.com/repos/{github_org}/{key.slug}/contents/README.md",
                json=data,
                headers=headers,
            )
            logger.info(json.dumps(readme_response.json(), default=str))
        return res
    except Exception as e:
        logging.exception(
            f"Error while sending request to update github repo: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon creating GitHub repository.",
        )
        raise


# Maybe better to get obj from efs? But then Lambda should be in VPC
def _get_obj_from_s3(key: KeyPath) -> bytes:
    try:
        if len(key.parts) == 2 and key.suffix.lower() == ".md":
            bucket_name = os.environ.get("IR_APKG_MD_BUCKET_NAME", "")
        else:
            bucket_name = os.environ.get("APKG_UPLOAD_BUCKET_NAME", "")
        resp = s3.get_object(
            Bucket=bucket_name,
            Key=str(key.s3_key),
        )
        logger.info(
            f"Response from s3.get_object(Bucket={bucket_name}, Key={key.s3_key}): "
            + json.dumps(resp, default=str)
        )
        contents = resp["Body"].read()
        # logger.info(f"Retrieved object as str: " + contents.decode("utf-8"))
        return contents
    except Exception as e:
        logging.exception(f"Error while getting object from s3: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while retrieving object from AWS.",
        )
        raise


def _get_from_github_repo(key: KeyPath, secret: GitHubSecret) -> requests.Response:
    """
    Gets the contents of a file in a repository.
    See API docs here:
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
    """
    try:
        github_org = secret["github_api_org"]
        res = requests.get(
            f"https://api.github.com/repos/{github_org}/{key.slug}/contents/{key.github_path}",
        )
        logger.info(json.dumps(res.json(), default=str))
        return res
    except Exception as e:
        logger.error(
            f"Unable to retrieve the previous version of the {key.s3_key} file. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while retrieving previous version of the file from GitHub.",
        )
        raise


def _put_to_github_repo(
    key: KeyPath,
    secret: GitHubSecret,
    contents: bytes,
    prev_v_sha: t.Optional[str],
    event,
) -> requests.Response:
    """
    Creates a new file or replaces an existing file in a repository.
    See API docs here:
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents
    """
    try:
        eventSource = event["Records"][0]["eventSource"]
        eventName = event["Records"][0]["eventName"]
        eventTime = event["Records"][0]["eventTime"]
        requestId = event["Records"][0]["responseElements"]["x-amz-request-id"]
        commit_message = f"{eventTime} [{requestId}] Perform action {eventSource}:{eventName} on '{key.s3_key}'"
    except (KeyError, IndexError):
        t = datetime.datetime.now().strftime("%d %b %Y at %H:%M")
        commit_message = "Update on " + t
    try:
        b64content = base64.b64encode(contents).decode()
        github_token = secret["github_api_token"]
        github_org = secret["github_api_org"]
    except Exception as e:
        logger.error(f"Unable to prepare contents of the file. Error: {repr(e)}")
        raise
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "message": commit_message,
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
            f"https://api.github.com/repos/{github_org}/{key.slug}/contents/{key.github_path}",
            json=data,
            headers=headers,
        )
        logger.info(json.dumps(res.json(), default=str))
        return res
    except Exception as e:
        logging.exception(
            f"Error while sending request to update github repo: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while sending request to update GitHub repo.",
        )
        raise


def _log_audit_event(key: KeyPath, status: int, msg: str) -> None:
    event = AuditEvent(
        slug=key.slug,
        module=ModuleEnum.GITHUB.value,
        filename=key.name,
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    logger.info(f"Audit event logged: {event}")
