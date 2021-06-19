from io import BytesIO, SEEK_SET
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
from PIL import Image
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

save_image_prefix = os.environ["SAVE_IMAGE_PREFIX"]
if save_image_prefix.endswith("/"):
    save_image_prefix = save_image_prefix[:-1]

s3 = boto3.client("s3")


def record_handler(record: typing.Dict[str, typing.Any]):
    notification = json.loads(record["body"])
    create_object_event = json.loads(notification["Message"])["Records"][0]
    logger.debug(create_object_event)

    bucket_name = create_object_event["s3"]["bucket"]["name"]
    object_key = create_object_event["s3"]["object"]["key"]

    head_response = s3.head_object(Bucket=bucket_name, Key=object_key)
    logger.debug(head_response)
    metadata = head_response["Metadata"]

    with BytesIO() as rbuf:
        s3.download_fileobj(
            Bucket=bucket_name,
            Key=object_key,
            Fileobj=rbuf,
        )
        with Image.open(rbuf) as image, BytesIO() as wbuf:
            image.save(wbuf, "WEBP")
            wbuf.seek(SEEK_SET)
            s3.upload_fileobj(
                Bucket=bucket_name,
                Key="/".join(
                    [
                        save_image_prefix,
                        "webp",
                        "original_size",
                        metadata["userid"],
                        metadata["imageid"],
                    ]
                ),
                Fileobj=wbuf,
                ExtraArgs={
                    "ContentType": "image/webp",
                    "Metadata": metadata,
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
