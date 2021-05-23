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


def record_handler(record: typing.Dict[str, typing.Any]):
    image_message_event = json.loads(record["body"])
    logger.debug(image_message_event)


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
