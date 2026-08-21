import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

BUCKET = "creds-poc-1787281630-felipe"
ROLE_ARN = "arn:aws:iam::536260290699:role/POC2"


def run(session, label):
    """Print which provider won, then do real S3 work with it."""
    print(f"\n--- {label} ---")

    try:
        creds = session.get_credentials()
    except (PartialCredentialsError, NoCredentialsError) as exc:
        print("resolution failed:", type(exc).__name__)
        return

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


base = boto3.Session(profile_name="felipe")

resp = base.client("sts").assume_role(
    RoleArn=ROLE_ARN,
    RoleSessionName="poc",
    DurationSeconds=900,
)
c = resp["Credentials"]
print("\nexpires:", c["Expiration"])

assumed = boto3.Session(
    aws_access_key_id=c["AccessKeyId"],
    aws_secret_access_key=c["SecretAccessKey"],
    aws_session_token=c["SessionToken"],
)

run(base, "base identity")
run(assumed, "assumed role")
