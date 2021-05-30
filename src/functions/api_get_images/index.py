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
)
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


tracer = Tracer()
logger = Logger()
app = ApiGatewayResolver()

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )


@app.get("/images")
@tracer.capture_method
def get_handler():
    return {"message": "OK"}


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_REST,
)
@tracer.capture_lambda_handler
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)
    logger.debug(context)
    return app.resolve(event, context)
