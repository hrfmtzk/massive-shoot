from aws_cdk import (
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
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
        original_image_created_topic: sns.Topic,
        table: dynamodb.Table,
        project_config: ProjectConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._webhook_to_bucket(
            bucket=bucket,
            project_config=project_config,
        )
        self._topic_to_table(
            topic=original_image_created_topic,
            bucket=bucket,
            table=table,
            project_config=project_config,
        )
        self._topic_to_resize_400(
            topic=original_image_created_topic,
            bucket=bucket,
            project_config=project_config,
        )
        self._topic_to_webp(
            topic=original_image_created_topic,
            bucket=bucket,
            project_config=project_config,
        )
        self._topic_to_webp_resize_400(
            topic=original_image_created_topic,
            bucket=bucket,
            project_config=project_config,
        )

    def _webhook_to_bucket(
        self,
        bucket: s3.Bucket,
        project_config: ProjectConfig,
    ) -> None:
        queue = sqs.Queue(
            self,
            "SaveImageQueue",
        )

        function = lambda_python.PythonFunction(
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
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:DeleteMessageBatch"],
                    resources=[queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        bucket.bucket_arn,
                        bucket.bucket_arn + "/*",
                    ],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=queue,
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
                "SAVE_IMAGE_QUEUE_URL": queue.queue_url,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:SendMessage"],
                    resources=[queue.queue_arn],
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

    def _topic_to_table(
        self,
        topic: sns.Topic,
        bucket: s3.Bucket,
        table: dynamodb.Table,
        project_config: ProjectConfig,
    ) -> None:
        queue = sqs.Queue(
            self,
            "SaveInfoQueue",
        )
        topic.add_subscription(subscriptions.SqsSubscription(queue))

        function = lambda_python.PythonFunction(
            self,
            "SaveInfoFunction",
            entry="src/functions/line_webhook_save_info",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(3),
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "TABLE_NAME": table.table_name,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:DeleteMessageBatch"],
                    resources=[queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:Get*",
                        "s3:List*",
                    ],
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
        function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=queue,
            ),
        )

    def _topic_to_resize_400(
        self,
        topic: sns.Topic,
        bucket: s3.Bucket,
        project_config: ProjectConfig,
    ) -> None:
        queue = sqs.Queue(
            self,
            "SaveResize400Queue",
        )
        topic.add_subscription(subscriptions.SqsSubscription(queue))

        function = lambda_python.PythonFunction(
            self,
            "SaveResize400Function",
            entry="src/functions/line_webhook_save_resize_400",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(10),
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "SAVE_IMAGE_PREFIX": project_config.save_image_prefix,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:DeleteMessageBatch"],
                    resources=[queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        bucket.bucket_arn,
                        bucket.bucket_arn + "/*",
                    ],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=queue,
            ),
        )

    def _topic_to_webp(
        self,
        topic: sns.Topic,
        bucket: s3.Bucket,
        project_config: ProjectConfig,
    ) -> None:
        queue = sqs.Queue(
            self,
            "SaveWebpQueue",
        )
        topic.add_subscription(subscriptions.SqsSubscription(queue))

        function = lambda_python.PythonFunction(
            self,
            "SaveWebpFunction",
            entry="src/functions/line_webhook_save_webp",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(10),
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "SAVE_IMAGE_PREFIX": project_config.save_image_prefix,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:DeleteMessageBatch"],
                    resources=[queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        bucket.bucket_arn,
                        bucket.bucket_arn + "/*",
                    ],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=queue,
            ),
        )

    def _topic_to_webp_resize_400(
        self,
        topic: sns.Topic,
        bucket: s3.Bucket,
        project_config: ProjectConfig,
    ) -> None:
        queue = sqs.Queue(
            self,
            "SaveWebpResize400Queue",
        )
        topic.add_subscription(subscriptions.SqsSubscription(queue))

        function = lambda_python.PythonFunction(
            self,
            "SaveWebpResize400Function",
            entry="src/functions/line_webhook_save_webp_resize_400",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(10),
            environment={
                "LOG_LEVEL": project_config.log_level,
                "POWERTOOLS_SERVICE_NAME": project_config.service_name,
                "SAVE_IMAGE_PREFIX": project_config.save_image_prefix,
                "SENTRY_DSN": project_config.sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["sqs:DeleteMessageBatch"],
                    resources=[queue.queue_arn],
                ),
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        bucket.bucket_arn,
                        bucket.bucket_arn + "/*",
                    ],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        function.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=queue,
            ),
        )
