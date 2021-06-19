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
from massive_shoot.config import ProjectConfig


load_dotenv(find_dotenv())

project_config = ProjectConfig()

region = os.environ.get("AWS_REGION", "ap-northeast-1")

app = cdk.App()

persistence = PersistenceStack(
    app,
    "Persistence",
    project_config=project_config,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

ApiStack(
    app,
    "Api",
    table=persistence.table,
    project_config=project_config,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

LineWebhookStack(
    app,
    "LineWebhook",
    bucket=persistence.bucket,
    original_image_created_topic=persistence.original_image_created_topic,
    table=persistence.table,
    project_config=project_config,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

HostingImageStack(
    app,
    "HostingImage",
    bucket=persistence.bucket,
    project_config=project_config,
    env=cdk.Environment(
        account=app.account,
        region=region,
    ),
)

app.synth()
