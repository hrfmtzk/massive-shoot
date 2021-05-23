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
    Response,
)
from linebot import (
    LineBotApi,
    WebhookHandler,
)
from linebot.exceptions import (
    InvalidSignatureError,
)
from linebot.models import (
    ImageMessage,
    MessageEvent,
    TextMessage,
    TextSendMessage,
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

line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])


@app.post("/callback")
@tracer.capture_method
def post_handler():
    signature = app.current_event.get_header_value("X-Line-Signature")
    body = app.current_event.body

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return Response(
            status_code=400,
            content_type="application/json",
            body=json.dumps({"message": "Invalid signature"}),
        )

    return {"message": "OK"}


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event: MessageEvent) -> None:
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text),
    )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event: MessageEvent) -> None:
    pass


@handler.default()
def handle_default(event) -> None:
    logger.debug(event.as_json_dict())


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_REST,
)
@tracer.capture_lambda_handler
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)
    return app.resolve(event, context)
