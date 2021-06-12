import typing

from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    aws_iam as iam,
    aws_s3 as s3,
    core as cdk,
)


class PersistenceStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        service_name: str,
        save_image_prefix: str,
        sentry_dsn: typing.Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_level = "DEBUG"
        sentry_dsn = sentry_dsn or ""

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=f"{service_name}-{self.account}-images",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                )
            ],
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        self.table = dynamodb.Table(
            self,
            "Table",
            table_name=service_name,
            partition_key=dynamodb.Attribute(
                name="UserId",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="ImageId",
                type=dynamodb.AttributeType.STRING,
            ),
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        resize_image_function = lambda_python.PythonFunction(
            self,
            "ResizeImageFunction",
            entry="src/functions/persistence_resize_image",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.seconds(10),
            environment={
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": service_name,
                "SAVE_IMAGE_PREFIX": save_image_prefix,
                "SENTRY_DSN": sentry_dsn,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        self.bucket.bucket_arn,
                        self.bucket.bucket_arn + "/*",
                    ],
                ),
            ],
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
        resize_image_function.add_event_source(
            lambda_event_sources.S3EventSource(
                bucket=self.bucket,
                events=[s3.EventType.OBJECT_CREATED],
                filters=[
                    s3.NotificationKeyFilter(
                        prefix=f"{save_image_prefix}/original",
                    )
                ],
            ),
        )
