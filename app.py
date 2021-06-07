#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from dotenv import (
    find_dotenv,
    load_dotenv,
)

from massive_shoot.api_stack import ApiStack
from massive_shoot.hosting_image_stack import HostingImageStack
from massive_shoot.line_webhook_stack import LineWebhookStack
from massive_shoot.persistence_stack import PersistenceStack


load_dotenv(find_dotenv())

region = os.environ.get("AWS_REGION", "ap-northeast-1")
service_name = os.environ.get("SERVICE_NAME", "massive-shoot")
line_channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
line_channel_secret = os.environ["LINE_CHANNEL_SECRET"]
line_login_channel_id = os.environ["LINE_LOGIN_CHANNEL_ID"]
hosting_image_domain = os.environ["HOSTING_IMAGE_DOMAIN"]
hosting_image_acm_arn = os.environ["HOSTING_IMAGE_ACM_ARN"]
sentry_dsn = os.environ.get("SENTRY_DSN")

app = cdk.App()

persistence = PersistenceStack(
    app,
    "Persistence",
    service_name=service_name,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

ApiStack(
    app,
    "Api",
    table=persistence.table,
    service_name=service_name,
    line_login_channel_id=line_login_channel_id,
    hosting_image_domain=hosting_image_domain,
    sentry_dsn=sentry_dsn,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

LineWebhookStack(
    app,
    "LineWebhook",
    bucket=persistence.bucket,
    table=persistence.table,
    service_name=service_name,
    channel_access_token=line_channel_access_token,
    channel_secret=line_channel_secret,
    sentry_dsn=sentry_dsn,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

HostingImageStack(
    app,
    "HostingImage",
    bucket=persistence.bucket,
    domain=hosting_image_domain,
    acm_arn=hosting_image_acm_arn,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

app.synth()
