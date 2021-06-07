import typing
from urllib import (
    error,
    parse,
    request,
)


FORBIDDEN_RESPONSE = {
    "status": "403",
    "statusDescription": "Forbidden",
    "body": "Forbidden",
}


def verify_token(token: str) -> bool:
    endpoint = "https://api.line.me/oauth2/v2.1/verify"
    params = {
        "access_token": token,
    }
    url = f"{endpoint}?{parse.urlencode(params)}"

    req = request.Request(url)
    try:
        with request.urlopen(req) as res:
            if res.getcode() != 200:
                return False
    except (error.HTTPError, error.URLError):
        return False

    return True


def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    request = event["Records"][0]["cf"]["request"]

    if request["method"] == "OPTIONS":
        return request

    headers = request["headers"]

    authorization: str = headers.get("authorization", [{"value": None}])[0][
        "value"
    ]
    if not (authorization and authorization.startswith("Bearer ")):
        return FORBIDDEN_RESPONSE

    token = authorization.split(" ", 1)[1]
    if not verify_token(token):
        return FORBIDDEN_RESPONSE

    return request
