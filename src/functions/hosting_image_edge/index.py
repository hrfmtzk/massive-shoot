from distutils.util import strtobool
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

save_image_prefix = ".images"
hosting_image_prefix = "images"

path_map = {
    # (support_webp, thumbnail): path
    (True, True): "webp/400/",
    (True, False): "webp/original_size/",
    (False, True): "original_format/400/",
    (False, False): "original/",
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


def change_origin_request(
    request: typing.Dict[str, typing.Any]
) -> typing.Dict[str, typing.Any]:
    uri: str = request["uri"]

    if not uri.startswith(f"/{hosting_image_prefix}"):
        return request

    headers = request["headers"]
    accept: str = headers.get("accept", [{"value": "*/*"}])[0]["value"]
    support_webp = False
    try:
        accept.split(";")[0].split(",").index("image/webp")
        support_webp = True
    except ValueError:
        pass

    query = parse.parse_qs(request["querystring"])
    thumbnail = strtobool(query.get("thumbnail", ["false"])[0])

    new_uri = f"/{save_image_prefix}/" + path_map[support_webp, thumbnail]

    user_id, image_id = uri[len(hosting_image_prefix) + 2 :].split("/")
    new_uri += f"{user_id}/{image_id}"

    request["uri"] = new_uri

    return request


def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    request = event["Records"][0]["cf"]["request"]

    request = change_origin_request(request)

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
