# https://aws.amazon.com/blogs/apn/how-an-aws-lambda-function-can-be-integrated-with-box-webhooks/
# It seems I cannot do step 6 (Content Manager) without paid Box version.
# https://support.box.com/hc/en-us/articles/360044197333-Using-the-Content-Manager

from box_sdk_gen import BoxClient, BoxJWTAuth, JWTConfig
import json
import pathlib
import subprocess


def _decrypt_box_config(config_path: str) -> str:
    fp = pathlib.Path(config_path)
    if not fp.exists():
        raise Exception(f"{config_path} was not found.")
    output = subprocess.run(f"sops -d {fp}".split(" "), capture_output=True)
    if output.returncode != 0:
        raise Exception(f"Decrypting {fp} failed.")
    return json.dumps(json.loads(output.stdout))


if __name__ == "__main__":
    config_path = "secrets/box_rblist_config.enc.json"
    folder_id = "0"
    config_json_str = _decrypt_box_config(config_path)
    jwt_config = JWTConfig.from_config_json_string(config_json_str)
    auth = BoxJWTAuth(config=jwt_config)
    client = BoxClient(auth=auth)
    fld = client.folders.get_folder_by_id(folder_id=folder_id)
    print("fld", fld)
    for item in client.folders.get_folder_items(folder_id=folder_id).entries:
        print(">", item.id, item.name, item.type)
