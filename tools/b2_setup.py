#!/usr/bin/env python3
"""Create the Instagram staging bucket using EXISTING B2 creds — no secrets touched by hand.

Reads S3-compatible creds already on this machine (~/Desktop/keys.env or Windows env vars:
AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / B2_ENDPOINT_URL), creates a private bucket
`openmontage-publish-staging` if absent, and writes ONLY the non-secret bucket name +
endpoint into OpenMontage/.env. Prints no credential values.

Run: python b2_setup.py
"""
import os
import re
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

BUCKET = "openmontage-publish-staging"
ENV = Path(__file__).parent.parent / "OpenMontage" / ".env"
KEYS_ENV = Path.home() / "Desktop" / "keys.env"


def set_env(key, value):
    text = ENV.read_text()
    if re.search(rf"(?m)^{key}=", text):
        text = re.sub(rf"(?m)^{key}=.*$", f"{key}={value}", text)
    else:
        text += f"\n{key}={value}\n"
    ENV.write_text(text)


def main():
    if KEYS_ENV.exists():
        load_dotenv(KEYS_ENV)  # into process env only; never printed
    key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("B2_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("B2_APP_KEY")
    endpoint = os.getenv("B2_ENDPOINT_URL") or os.getenv("B2_S3_ENDPOINT")
    if not (key and secret and endpoint):
        sys.exit("No B2 creds found in keys.env or env (need AWS_ACCESS_KEY_ID / "
                 "AWS_SECRET_ACCESS_KEY / B2_ENDPOINT_URL).")

    s3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=key, aws_secret_access_key=secret)
    try:
        s3.head_bucket(Bucket=BUCKET)
        print(f"Bucket already exists: {BUCKET}")
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        print(f"Created private bucket: {BUCKET}")

    set_env("B2_BUCKET", BUCKET)
    set_env("B2_S3_ENDPOINT", endpoint)
    print(f"Wrote B2_BUCKET + B2_S3_ENDPOINT to {ENV}")
    print("B2 keys stay in keys.env — publish.py reads them at runtime, not stored in .env.")


if __name__ == "__main__":
    main()
