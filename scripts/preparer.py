import sys
import os

# Get the parent directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.preparer.main import lambda_handler


if __name__ == "__main__":
    event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "eu-west-1",
                "eventTime": "2024-06-01T10:01:01.100Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {"principalId": "AWS:AROAVK5GEQE3275W6UTUO:preparer"},
                "requestParameters": {"sourceIPAddress": "10.10.2.149"},
                "responseElements": {
                    "x-amz-request-id": "7MMJ7WJPN7GM5KYN",
                    "x-amz-id-2": "E3m/Eudcp6Z7vZh9Ex1blHs1bHy7ajDl71V6BBnXFD5dwiHqE+ylOE578E4+ShRpve8ctI5y9abpl4QbtsPrl3XhN8bxbgiF",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "tf-s3-lambda-20240531090332003100000001",
                    "bucket": {
                        "name": "dgtmon-dev-apkg-upload",
                        "ownerIdentity": {"principalId": "A13XBETHGUR4IG"},
                        "arn": "arn:aws:s3:::dgtmon-dev-apkg-upload",
                    },
                    "object": {
                        "key": "my-slug/test.docx",
                        "size": 278,
                        "eTag": "3647c11ea643861bb23a8dd628cd0642",
                        "sequencer": "00665DF6D32A167391",
                    },
                },
            }
        ]
    }
    context = {}
    lambda_handler(event, context)
