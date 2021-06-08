import os
import typing

from aws_lambda_powertools import (
    Logger,
    Tracer,
)
import requests
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


tracer = Tracer()
logger = Logger()

channel_id = os.environ["LINE_LOGIN_CHANNEL_ID"]

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )


class UnverifiedError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = message


def verify_token(token: str) -> bool:
    response = requests.get(
        url="https://api.line.me/oauth2/v2.1/verify",
        params={
            "access_token": token,
        },
    )
    response_json = response.json()
    logger.debug(response_json)

    if response.status_code == 200:
        if response_json["client_id"] == channel_id:
            return True
        else:
            raise UnverifiedError("invalie access token")
    elif response.status_code == 400:
        raise UnverifiedError(response_json["error_description"])

    raise UnverifiedError("unknown authorization error")


def get_profile(token: str) -> typing.Dict[str, typing.Union[str, None]]:
    response = requests.get(
        url="https://api.line.me/v2/profile",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    response_json = response.json()
    logger.debug(response_json)
    return {
        "user_id": response_json.get("userId"),
        "display_name": response_json.get("displayName"),
        "picture_url": response_json.get("pictureUrl"),
    }


def generate_policy(
    event,
    principal_id: str,
    allow: bool,
    context: typing.Optional[typing.Dict[str, str]],
) -> typing.Dict[str, typing.Any]:

    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow" if allow else "Deny",
                    "Resource": event["methodArn"],
                },
            ],
        },
    }
    if context:
        policy["context"] = context

    logger.debug(policy)

    return policy


@tracer.capture_lambda_handler
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)

    token: str = event["authorizationToken"]

    context = {}
    if not token.startswith("Bearer "):
        verify = False
        context["message"] = "Authorization type is not Bearer"
    else:
        token = token.split(" ", 1)[1]
        try:
            verify = verify_token(token)
        except UnverifiedError as e:
            verify = False
            context["message"] = e.message

    if verify:
        context = get_profile(token)

    return generate_policy(
        event,
        context.get("user_id", "anonymous"),
        allow=verify,
        context=context,
    )
