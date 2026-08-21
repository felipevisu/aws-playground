## Step 1 - Prove that I can talk with AWS

**Code**
```python
import boto3

session = boto3.Session()
print(session.client("sts").get_caller_identity())
```

**Run**
```bash
python main.py
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
AWS_ACCESS_KEY_ID=AKIABOGUS000000000 AWS_SECRET_ACCESS_KEY=nope python main.py
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