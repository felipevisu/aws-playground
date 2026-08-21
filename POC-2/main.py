import boto3

session = boto3.Session()
print(session.client("sts").get_caller_identity())
