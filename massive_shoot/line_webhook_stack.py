import typing

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    core as cdk,
)


class LineWebhookStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        service_name: str,
        channel_access_token: str,
        channel_secret: str,
        sentry_dsn: typing.Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_level = "DEBUG"
        sentry_dsn = sentry_dsn or ""

        post_callback_function = lambda_python.PythonFunction(
            self,
            "PostCallbackFunction",
            entry="src/functions/line_webhook_post_callback",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": service_name,
                "CHANNEL_ACCESS_TOKEN": channel_access_token,
                "CHANNEL_SECRET": channel_secret,
                "SENTRY_DSN": sentry_dsn,
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        api = apigateway.RestApi(
            self,
            "Api",
        )

        callback_resource = api.root.add_resource("callback")
        callback_resource.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(
                handler=post_callback_function,
            ),
        )
