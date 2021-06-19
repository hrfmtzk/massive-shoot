import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="massive_shoot",
    version="0.0.1",
    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="author",
    package_dir={"": "massive_shoot"},
    packages=setuptools.find_packages(where="massive_shoot"),
    install_requires=[
        "aws-cdk.aws-apigateway==1.108.1",
        "aws-cdk.aws-certificatemanager==1.108.1",
        "aws-cdk.aws-cloudfront==1.108.1",
        "aws-cdk.aws-cloudfront-origins==1.108.1",
        "aws-cdk.aws-dynamodb==1.108.1",
        "aws-cdk.aws-iam==1.108.1",
        "aws-cdk.aws-lambda==1.108.1",
        "aws-cdk.aws-lambda-event-sources==1.108.1",
        "aws-cdk.aws-lambda-python==1.108.1",
        "aws-cdk.aws-logs==1.108.1",
        "aws-cdk.aws-s3==1.108.1",
        "aws-cdk.aws-s3-notifications==1.108.1",
        "aws-cdk.aws-sns==1.108.1",
        "aws-cdk.aws-sqs==1.108.1",
        "aws-cdk.core==1.108.1",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
