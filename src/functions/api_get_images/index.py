import json
import os
import typing

from aws_lambda_powertools import (
    Logger,
    Tracer,
)
from aws_lambda_powertools.logging import (
    correlation_paths,
)
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    CORSConfig,
    Response,
)
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from models import image


tracer = Tracer()
logger = Logger()

cors_config = CORSConfig()
app = ApiGatewayResolver(cors=cors_config)

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )

image_base_url = os.environ["IMAGE_BASE_URL"]
if not image_base_url.endswith("/"):
    image_base_url += "/"


@app.get("/images")
@tracer.capture_method
def get_handler():
    images = [
        image.convert_respones_image(item, image_base_url)
        for item in image.get_all_items()
    ]
    return Response(
        status_code=200,
        content_type="application/json",
        body=json.dumps(images, separators=(",", ":")),
        headers={
            "X-Content-Length": len(images),
        },
    )


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_REST,
)
@tracer.capture_lambda_handler
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)
    logger.debug(context)
    return app.resolve(event, context)
