# import io
# from botocore.stub import Stubber
# def stub_out_requests(stubber: Stubber) -> None:
#     content = ""
#     data = io.BytesIO()
#     data.write(content.encode("utf-8"))
#     data.seek(0)
#     responses = [
#         {
#             "call": "head_object",
#             "expected_params": {
#                 "Bucket": "bucket_name",
#                 "Key": "key2",
#             },
#             "response": {
#                 "ContentLength": 10,
#                 "ContentType": "utf-8",
#                 "ResponseMetadata": {
#                     "Bucket": "bucket_name",
#                 },
#             },
#         },
#         {
#             "call": "get_object",
#             "expected_params": {
#                 "Bucket": "bucket_name",
#                 "Key": "key2",
#             },
#             "response": {
#                 "ContentLength": len(content),
#                 "ContentType": "utf-8",
#                 "Body": data,
#                 "ResponseMetadata": {
#                     "Bucket": "bucket_name",
#                 },
#             },
#         },
#     ]
#     for rsp in responses:
#         stubber.add_response(rsp["call"], rsp["response"], rsp["expected_params"])
