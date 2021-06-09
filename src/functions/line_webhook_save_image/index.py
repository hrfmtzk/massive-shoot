from io import BytesIO
import json
import os
import typing

from aws_lambda_powertools import (
    Logger,
    Tracer,
)
from aws_lambda_powertools.utilities.batch import (
    PartialSQSProcessor,
    batch_processor,
)
import boto3
from linebot import LineBotApi
import sentry_sdk
from sentry_sdk import capture_exception
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


tracer = Tracer()
logger = Logger()

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )

line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])

save_image_prefix = os.environ["SAVE_IMAGE_PREFIX"]
if save_image_prefix.endswith("/"):
    save_image_prefix = save_image_prefix[:-1]

bucket_name = os.environ["BUCKET_NAME"]
s3 = boto3.client("s3")

table_name = os.environ["TABLE_NAME"]
dynamodb = boto3.client("dynamodb")


def record_handler(record: typing.Dict[str, typing.Any]):
    image_message_event = json.loads(record["body"])
    logger.debug(image_message_event)

    message_id = image_message_event["message"]["id"]
    image_id = f"L{message_id}"
    user_id = image_message_event["source"]["userId"]
    unix_time = image_message_event["timestamp"] / 1000.0

    object_key = f"{save_image_prefix}/original/{user_id}/{image_id}"
    message_content = line_bot_api.get_message_content(message_id)

    s3.upload_fileobj(
        Fileobj=BytesIO(message_content.content),
        Bucket=bucket_name,
        Key=object_key,
        ExtraArgs={
            "ContentType": message_content.content_type,
        },
    )

    dynamodb.put_item(
        TableName=table_name,
        Item={
            "UserId": {"S": user_id},
            "ImageId": {"S": image_id},
            "Created": {"N": str(unix_time)},
            "ContentType": {"S": message_content.content_type},
            "ObjectKey": {"S": object_key},
        },
    )


class SQSProcessor(PartialSQSProcessor):
    def failure_handler(
        self, record: typing.Any, exception: typing.Tuple
    ) -> typing.Tuple:
        if sentry_dsn:
            capture_exception()
        logger.exception("got exception while processing SQS message")
        return super().failure_handler(record, exception)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@batch_processor(record_handler=record_handler, processor=SQSProcessor())
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)
    return {"statusCode": 200}
