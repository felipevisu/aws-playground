## Step 1 - Prove that I can talk with AWS

**Code**
```python
import boto3

session = boto3.Session()
print(session.client("sts").get_caller_identity())
```

**Run**
```bash
python step1.py
```

**Output**
```json
{
    "UserId": "AIDAXZW42VCFU3JKN5YR3", 
    "Account": "536260290699", 
    "Arn": "arn:aws:iam::536260290699:user/felipe-admin", 
    "ResponseMetadata": {
        "RequestId": "1020a616-1656-464c-9563-6690998cea47", 
        "HTTPStatusCode": 200, 
        "HTTPHeaders": {
            "x-amzn-requestid": "1020a616-1656-464c-9563-6690998cea47", "x-amz-sts-extended-request-id": "MTp1cy1lYXN0LTE6UzoxNzg3MjgxNzg2ODg5OlI6WnRlMGM0am8=", "content-type": "text/xml", 
            "content-length": "409", 
            "date": "Fri, 21 Aug 2026 03:09:46 GMT"
        }, 
        "RetryAttempts": 0
    }
}
```

## Step 2 - Running with junk env vars

```bash
AWS_ACCESS_KEY_ID=AKIABOGUS000000000 AWS_SECRET_ACCESS_KEY=nope python script1.py
```

**Output**
```bash
  File "/Users/felipefaria/Playgroung/aws-playground/POC-2/main.py", line 4, in <module>
    print(session.client("sts").get_caller_identity())
          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/felipefaria/Playgroung/aws-playground/POC-2/venv/lib/python3.14/site-packages/botocore/client.py", line 606, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/felipefaria/Playgroung/aws-playground/POC-2/venv/lib/python3.14/site-packages/botocore/context.py", line 123, in wrapper
    return func(*args, **kwargs)
  File "/Users/felipefaria/Playgroung/aws-playground/POC-2/venv/lib/python3.14/site-packages/botocore/client.py", line 1094, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.exceptions.ClientError: An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation: The security token included in the request is invalid.
```

## Step 3 - Uploading a file

**Code**
```python
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
s3.put_object(Bucket="YOUR-BUCKET", Key="poc/hello.txt", Body=b"hello\n")
print("uploaded")
```

**Run**
```bash
python script2.py
```

**Output**
```bash
provider: shared-credentials-file
arn:aws:iam::536260290699:user/felipe-admin
  creds-poc-1787281630-felipe
  poc-iam-felipefaria-01
uploaded
```

## Step 4 - Reusable function

**Output**
```bash
--- default chain ---
provider: shared-credentials-file
arn     : arn:aws:iam::536260290699:user/felipe-admin
buckets : 2
uploaded

--- explicit profile ---
provider: shared-credentials-file
arn     : arn:aws:iam::330890114384:user/felipevisu
buckets : 4
FAILED: AccessDenied

--- hardcoded junk ---
provider: explicit
FAILED: InvalidClientTokenId
```
## Step 5 - Assume role

Role `POC2` trusts `felipe-admin` and has only `AmazonS3ReadOnlyAccess` attached.

**Code**
```python
ROLE_ARN = "arn:aws:iam::536260290699:role/POC2"

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
```

**Run**
```bash
python script4.py
```

**Output**
```bash
expires: 2026-08-21 13:12:36+00:00

--- base identity ---
provider: shared-credentials-file
arn     : arn:aws:iam::536260290699:user/felipe-admin
buckets : 2
uploaded

--- assumed role ---
provider: explicit
arn     : arn:aws:sts::536260290699:assumed-role/POC2/poc
buckets : 2
FAILED: AccessDenied
```

**Notes**
- `assume_role` returns temporary creds (15 min here) — note the `SessionToken`, absent from the long-lived user keys.
- Identity changes: `user/felipe-admin` → `assumed-role/POC2/poc`. Same account, different permissions.
- `list_buckets` works, `put_object` fails: role policy is read-only (`Get*`/`List*`), no `s3:PutObject`. Least privilege in action — the admin user can write, the role it assumed cannot.
