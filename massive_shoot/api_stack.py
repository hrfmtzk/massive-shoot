import json

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    core as cdk,
)

from massive_shoot.config import ProjectConfig


class ApiStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        table: dynamodb.Table,
        project_config: ProjectConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        authorizer_function = lambda_python.PythonFunction(
            self,
            "AuthorizerFunction",
            entry="src/functions/api_authorizer",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(3),
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "LINE_LOGIN_CHANNEL_ID": project_config.line_login_channel_id,
                "SENTRY_DSN": project_config.sentry_dsn,
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
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "TABLE_NAME": table.table_name,
                "TABLE_REGION": self.region,
                "IMAGE_BASE_URL": "https://"
                + project_config.hosting_image_domain,
                "IMAGE_PREFIX": project_config.hosting_image_prefix,
                "SENTRY_DSN": project_config.sentry_dsn,
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
