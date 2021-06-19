from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_s3_notifications as notifications,
    aws_sns as sns,
    core as cdk,
)

from massive_shoot.config import ProjectConfig


class PersistenceStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        project_config: ProjectConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.original_image_created_topic = sns.Topic(
            self,
            "OriginalImageCreatedTopic",
        )

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=f"{project_config.service_name}-{self.account}-images",
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
        self.bucket.add_object_created_notification(
            notifications.SnsDestination(self.original_image_created_topic),
            s3.NotificationKeyFilter(
                prefix=f"{project_config.save_image_prefix}/original/",
            ),
        )

        self.table = dynamodb.Table(
            self,
            "Table",
            table_name=project_config.service_name,
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
