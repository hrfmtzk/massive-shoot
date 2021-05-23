#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from dotenv import (
    find_dotenv,
    load_dotenv,
)

from massive_shoot.line_webhook_stack import LineWebhookStack


load_dotenv(find_dotenv())

region = os.environ.get("AWS_REGION", "ap-northeast-1")
service_name = os.environ.get("SERVICE_NAME", "massive-shoot")
line_channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
line_channel_secret = os.environ["LINE_CHANNEL_SECRET"]
sentry_dsn = os.environ.get("SENTRY_DSN")

app = cdk.App()

LineWebhookStack(
    app,
    "LineWebhook",
    service_name=service_name,
    channel_access_token=line_channel_access_token,
    channel_secret=line_channel_secret,
    sentry_dsn=sentry_dsn,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

app.synth()
