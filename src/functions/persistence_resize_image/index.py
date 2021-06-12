from io import BytesIO, SEEK_SET
import os

from aws_lambda_powertools import (
    Logger,
    Tracer,
)
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    S3Event,
)
import boto3
from PIL import Image
import sentry_sdk
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


def process_image(
    image: Image,
    bucket_name: str,
    user_id: str,
    file_name: str,
) -> None:

    content_type = f"image/{image.format.lower()}"

    # original size webp
    with BytesIO() as buf:
        image.save(buf, "WEBP")
        buf.seek(SEEK_SET)
        object_key = "/".join(
            [save_image_prefix, "webp", "original_size", user_id, file_name]
        )
        s3.upload_fileobj(
            Fileobj=buf,
            Bucket=bucket_name,
            Key=object_key,
            ExtraArgs={
                "ContentType": "image/webp",
            },
        )

    image_400 = image.copy()
    image_400.thumbnail((400, 400))
    # 400 original format
    with BytesIO() as buf:
        image_400.save(buf, image.format)
        buf.seek(SEEK_SET)
        object_key = "/".join(
            [save_image_prefix, "original_format", "400", user_id, file_name]
        )
        s3.upload_fileobj(
            Fileobj=buf,
            Bucket=bucket_name,
            Key=object_key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

    # 400 webp
    with BytesIO() as buf:
        image_400.save(buf, "WEBP")
        buf.seek(SEEK_SET)
        object_key = "/".join(
            [save_image_prefix, "webp", "400", user_id, file_name]
        )
        s3.upload_fileobj(
            Fileobj=buf,
            Bucket=bucket_name,
            Key=object_key,
            ExtraArgs={
                "ContentType": "image/webp",
            },
        )


@tracer.capture_lambda_handler
@event_source(data_class=S3Event)
def lambda_handler(event: S3Event, context) -> None:
    logger.debug(event)

    bucket_name = event.bucket_name

    for record in event.records:
        object_key = record.s3.get_object.key
        paths = object_key.split("/")
        file_name = paths[-1]
        user_id = paths[-2]

        with BytesIO() as image_buffer:
            s3.download_fileobj(bucket_name, object_key, image_buffer)

            with Image.open(image_buffer) as image:
                process_image(
                    image=image,
                    bucket_name=bucket_name,
                    user_id=user_id,
                    file_name=file_name,
                )

    return
