## Journal

# IAM Lab — Quick Version (CLI)

Lean runbook. Each block is copy-paste. Regional resources in `us-east-1`. IAM is global.

Set your variables first:

```bash
export BUCKET=poc-iam-felipe-2026        # replace with your own unique name
export REGION=us-east-1
```

---

## 1. Root: MFA and no keys

Console only (you can't set root MFA via CLI):
- Log in as root → account name → **Security credentials** → **Assign MFA device** → authenticator app.
- Delete any root access keys. Never use root again.

---

## 2. Admin (group + user + you on the CLI)

```bash
# admin group
aws iam create-group --group-name admins
aws iam attach-group-policy --group-name admins \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# admin user in the group
aws iam create-user --user-name felipe-admin
aws iam add-user-to-group --user-name felipe-admin --group-name admins

# access key for the CLI (save the SecretAccessKey — shown only once)
aws iam create-access-key --user-name felipe-admin

# configure the CLI as this user and confirm
aws configure                          # paste the keys, region us-east-1
aws sts get-caller-identity            # ARN should end in user/felipe-admin
```

Enable MFA on `felipe-admin` in the Console too.

---

## 3. Target bucket

```bash
aws s3 mb s3://$BUCKET --region $REGION
echo "test secret" > test.txt
aws s3 cp test.txt s3://$BUCKET/test.txt
```

---

## 4. Read-only user (least privilege)

```bash
# custom policy: only list the bucket and read its objects
cat > read-only.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "List", "Effect": "Allow", "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::$BUCKET" },
    { "Sid": "Read", "Effect": "Allow", "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET/*" }
  ]
}
EOF

POLICY_ARN=$(aws iam create-policy --policy-name read-only-$BUCKET \
  --policy-document file://read-only.json \
  --query 'Policy.Arn' --output text)

# user + policy attached directly (no group, on purpose)
aws iam create-user --user-name reader-s3
aws iam attach-user-policy --user-name reader-s3 --policy-arn $POLICY_ARN

# reader key on a separate profile
aws iam create-access-key --user-name reader-s3
aws configure --profile reader          # paste the reader keys
```

Test (2 pass, 2 fail with AccessDenied):

```bash
aws s3 ls s3://$BUCKET --profile reader                               # OK
aws s3 cp s3://$BUCKET/test.txt downloaded.txt --profile reader       # OK
aws s3 cp test.txt s3://$BUCKET/other.txt --profile reader            # DENY (no Allow to write)
aws s3 ls --profile reader                                            # DENY (no Allow to list all)
```

> Failure = **absence of Allow**, not a Deny. IAM's default is to deny.

---

## 5. Role for EC2 + instance profile

```bash
# trust policy: who can assume it (the EC2 service)
cat > trust-ec2.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
EOF

# create role, attach the SAME read policy
aws iam create-role --role-name ec2-read-s3 \
  --assume-role-policy-document file://trust-ec2.json
aws iam attach-role-policy --role-name ec2-read-s3 --policy-arn $POLICY_ARN

# instance profile (the "envelope" that plugs the role into EC2)
aws iam create-instance-profile --instance-profile-name ec2-read-s3
aws iam add-role-to-instance-profile \
  --instance-profile-name ec2-read-s3 --role-name ec2-read-s3
```

---

## 6. EC2 reads S3 with no credentials

Launch a **t2.micro / Amazon Linux 2023** and attach the instance profile `ec2-read-s3`
(Console: Advanced details → IAM instance profile). Or via CLI, if you already have an AMI/subnet:

```bash
# example — adjust --image-id, --key-name, --subnet-id to your environment
aws ec2 run-instances \
  --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --instance-type t2.micro \
  --iam-instance-profile Name=ec2-read-s3 \
  --region $REGION
```

**Inside the instance** (Connect → EC2 Instance Connect), without typing any key:

```bash
aws sts get-caller-identity          # ARN: .../assumed-role/ec2-read-s3/<instance>
aws s3 ls s3://$BUCKET
aws s3 cp s3://$BUCKET/test.txt /tmp/test.txt && cat /tmp/test.txt

# (optional) see the temporary credentials coming from the metadata service:
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/ec2-read-s3
```

---

## 7. Anti-example (do it wrong to feel it)

Still on the EC2:

```bash
export AWS_ACCESS_KEY_ID=<reader-s3 key>
export AWS_SECRET_ACCESS_KEY=<reader-s3 secret>
aws s3 ls s3://$BUCKET     # works...
env | grep AWS             # ...but the key sits in plain text in the environment
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY   # clean up!
```

Role: temporary credential, rotates itself, gone if leaked.
Access key in env: static, exposed, valid until someone revokes it. **Always use a role.**

---

## 8. CloudTrail (turn it on and find yourself)

```bash
# bucket for logs + multi-region trail
aws s3 mb s3://$BUCKET-logs --region $REGION
aws cloudtrail create-trail --name trail-poc \
  --s3-bucket-name $BUCKET-logs --is-multi-region-trail
aws cloudtrail start-logging --name trail-poc
```

Then: Console → **CloudTrail → Event history** → filter by `felipe-admin`,
`ConsoleLogin`, `ListBuckets`, `AssumeRole`. Find the `AssumeRole` from your EC2.

---

## 9. Cleanup (keep cost ~zero)

```bash
# EC2 first (only thing billed per hour) — grab the ID and terminate:
aws ec2 terminate-instances --instance-ids <i-xxxx>

# S3
aws s3 rb s3://$BUCKET --force
aws s3 rb s3://$BUCKET-logs --force

# CloudTrail
aws cloudtrail delete-trail --name trail-poc

# IAM (detach before deleting)
aws iam remove-role-from-instance-profile --instance-profile-name ec2-read-s3 --role-name ec2-read-s3
aws iam delete-instance-profile --instance-profile-name ec2-read-s3
aws iam detach-role-policy --role-name ec2-read-s3 --policy-arn $POLICY_ARN
aws iam delete-role --role-name ec2-read-s3
aws iam detach-user-policy --user-name reader-s3 --policy-arn $POLICY_ARN
aws iam delete-user --user-name reader-s3
aws iam delete-policy --policy-arn $POLICY_ARN
# delete stray access keys and, if this was just a lab, felipe-admin/admins group
```

> Keep **root with MFA**.

---

## Exam concepts (quick recap)

- **Identity policy vs resource policy.** Identity policy attaches to a user/group/role ("what this identity can do"); resource policy attaches to the resource, e.g. an S3 bucket policy ("who can do what on this resource"). They add up; access is the union of Allows minus any Deny.
- **User vs group vs role.** User = permanent identity with long-term credentials. Group = just a way to batch-apply policy to users (no credentials, can't be assumed). Role = identity with no fixed credentials, assumed temporarily, hands out short-lived credentials.
- **Instance profile.** The container that attaches a role to an EC2 instance. The role holds the permissions; the instance profile plugs it in.
- **Least privilege.** Start from nothing, add only what's needed — that was `reader-s3`.
- **Explicit Deny vs absence of Allow.** IAM default = deny. No Allow → denied. An explicit Deny always wins over any Allow. Order: explicit Deny > Allow > implicit deny.
- **IAM is global.** Users, groups, roles and policies have no region. S3, EC2 and CloudTrail are regional.