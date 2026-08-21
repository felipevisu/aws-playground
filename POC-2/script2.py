import boto3

session = boto3.Session()

creds = session.get_credentials()
print("provider:", creds.method)
print(session.client("sts").get_caller_identity()["Arn"])

s3 = session.client("s3")

# list
for b in s3.list_buckets()["Buckets"]:
    print(" ", b["Name"])


# upload
s3.put_object(
    Bucket="creds-poc-1787281630-felipe", Key="poc/hello.txt", Body=b"hello\n"
)
print("uploaded")
