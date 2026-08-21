import boto3

session = boto3.Session(profile_name="felipe")
s3 = session.client("s3")

response = s3.list_buckets()

for bucket in response["Buckets"]:
    print(f"{bucket['Name']}\t{bucket['CreationDate']}")