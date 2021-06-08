import json
import typing

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
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
        table: dynamodb.Table,
        service_name: str,
        line_login_channel_id: str,
        hosting_image_domain: str,
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

        layer = lambda_python.PythonLayerVersion(
            self,
            "Layer",
            entry="src/layers/api_package",
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_8],
        )

        get_images_function = lambda_python.PythonFunction(
            self,
            "GetImagesFunction",
            entry="src/functions/api_get_images",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            layers=[layer],
            timeout=cdk.Duration.seconds(3),
            environment={
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": service_name,
                "TABLE_NAME": table.table_name,
                "TABLE_REGION": self.region,
                "IMAGE_BASE_URL": "https://" + hosting_image_domain,
                "SENTRY_DSN": sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:BatchGetItem",
                        "dynamodb:Describe*",
                        "dynamodb:List*",
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                    ],
                    resources=[table.table_arn],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        api = apigateway.RestApi(
            self,
            "Api",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
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
