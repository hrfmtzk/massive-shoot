from aws_cdk import (
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sqs as sqs,
    core as cdk,
)

from massive_shoot.config import ProjectConfig


class LineWebhookStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        bucket: s3.Bucket,
        table: dynamodb.Table,
        project_config: ProjectConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        save_image_queue = sqs.Queue(
            self,
            "SaveImageQueue",
        )

        save_image_function = lambda_python.PythonFunction(
            self,
            "SaveImageFunction",
            entry="src/functions/line_webhook_save_image",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(10),
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "CHANNEL_ACCESS_TOKEN": project_config.line_channel_access_token,  # noqa
                "SAVE_IMAGE_PREFIX": project_config.save_image_prefix,
                "BUCKET_NAME": bucket.bucket_name,
                "TABLE_NAME": table.table_name,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:DeleteMessageBatch"],
                    resources=[save_image_queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        bucket.bucket_arn,
                        bucket.bucket_arn + "/*",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:*"],
                    resources=[table.table_arn],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        save_image_function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=save_image_queue,
            ),
        )

        post_callback_function = lambda_python.PythonFunction(
            self,
            "PostCallbackFunction",
            entry="src/functions/line_webhook_post_callback",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "CHANNEL_ACCESS_TOKEN": project_config.line_channel_access_token,  # noqa
                "CHANNEL_SECRET": project_config.line_channel_secret,
                "SAVE_IMAGE_QUEUE_URL": save_image_queue.queue_url,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:SendMessage"],
                    resources=[save_image_queue.queue_arn],
                ),
            ],
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
