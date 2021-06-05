from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    core as cdk,
)


class PersistenceStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        service_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=f"{service_name}-{self.account}-images",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
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
