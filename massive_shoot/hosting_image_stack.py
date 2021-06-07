from aws_cdk import (
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_lambda as lambda_,
    aws_s3 as s3,
    core as cdk,
)
from aws_cdk.aws_cloudfront import experimental


class HostingImageStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        bucket: s3.Bucket,
        domain: str,
        acm_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        function = experimental.EdgeFunction(
            self,
            "EdgeFunction",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("src/functions/hosting_image_edge/"),
            timeout=cdk.Duration.seconds(1),
        )

        cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    bucket=bucket,
                ),
                edge_lambdas=[
                    cloudfront.EdgeLambda(
                        function_version=function.current_version,
                        event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,  # noqa
                    ),
                ],
            ),
            domain_names=[domain],
            certificate=acm.Certificate.from_certificate_arn(
                self,
                "Certification",
                certificate_arn=acm_arn,
            ),
        )
