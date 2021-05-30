import json
import typing

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    core as cdk,
)


class ApiStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        service_name: str,
        line_login_channel_id: str,
        sentry_dsn: typing.Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_level = "DEBUG"

        authorizer_function = lambda_python.PythonFunction(
            self,
            "AuthorizerFunction",
            entry="src/functions/api_authorizer",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(3),
            environment={
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": service_name,
                "LINE_LOGIN_CHANNEL_ID": line_login_channel_id,
                "SENTRY_DSN": sentry_dsn,
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        authorizer = apigateway.TokenAuthorizer(
            self,
            "Authorizer",
            handler=authorizer_function,
        )

        get_images_function = lambda_python.PythonFunction(
            self,
            "GetImagesFunction",
            entry="src/functions/api_get_images",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(3),
            environment={
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": service_name,
                "SENTRY_DSN": sentry_dsn,
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        api = apigateway.RestApi(
            self,
            "Api",
        )
        api.add_gateway_response(
            "AccessDenied",
            type=apigateway.ResponseType.ACCESS_DENIED,
            status_code="403",
            templates={
                "application/json+ploblem": json.dumps(
                    {"message": "$context.authorizer.message"}
                ),
            },
        )

        images_resource = api.root.add_resource("images")
        images_resource.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(
                handler=get_images_function,
            ),
            authorizer=authorizer,
        )
