import boto3
from botocore.exceptions import ClientError

BUCKET = "creds-poc-1787281630-felipe"


def run(session, label):
    print(f"\n--- {label} ---")

    creds = session.get_credentials()
    if creds is None:
        print("no credentials resolved")
        return

    print("provider:", creds.method)

    try:
        print("arn     :", session.client("sts").get_caller_identity()["Arn"])
        s3 = session.client("s3")
        print("buckets :", len(s3.list_buckets()["Buckets"]))
        s3.put_object(Bucket=BUCKET, Key="poc/hello.txt", Body=b"hello\n")
        print("uploaded")
    except ClientError as exc:
        print("FAILED:", exc.response["Error"]["Code"])


run(boto3.Session(), "default chain")
run(boto3.Session(profile_name="felipe"), "explicit profile")
run(
    boto3.Session(
        aws_access_key_id="AKIABOGUS000000000",
        aws_secret_access_key="nope",
    ),
    "hardcoded junk",
)
