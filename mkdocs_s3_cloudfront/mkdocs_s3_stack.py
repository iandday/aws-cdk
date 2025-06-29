import sys
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_lambda as lambda_,
    CfnParameter,
    CfnOutput,
)
from constructs import Construct
import os

from typing import cast
from aws_cdk.aws_iam import IPrincipal
from aws_cdk.aws_lambda import IVersion
from typing import cast
from dotenv import dotenv_values



class MkdocsS3CloudfrontStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config = {**dotenv_values(".env"),  **os.environ}
        account = config.get('CDK_DEFAULT_ACCOUNT', None)
        region = config.get('CDK_DEFAULT_REGION', None)
        
        if account and region is None:
            print("Please set the CDK_DEFAULT_ACCOUNT and CDK_DEFAULT_REGION environment variables.")
            sys.exit(1)

        bucket_name = CfnParameter(
            self,
            "BucketName",
            description="The name for your S3 bucket.",
            type="String",
            default=f'mkdocs-bucket-{account}-{region}'
        )
        index_page = CfnParameter(
            self,
            "IndexPage",
            description="The page for your index document.",
            type="String",
            default="index.html"
        )


        # S3 Bucket
        bucket = s3.Bucket(
            self, 
            "Bucket", 
            bucket_name=bucket_name.value_as_string,
            access_control=s3.BucketAccessControl.PRIVATE,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        rewrite_function = lambda_.Function(
            self,
            "RewriteFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json

def handler(event, context):
    # Extract the request from the CloudFront event that is sent to Lambda@Edge
    request = event['Records'][0]['cf']['request']
    
    # Extract the URI from the request
    old_uri = request['uri']
    
    # Match any '/' that occurs at the end of a URI. Replace it with a default index
    if old_uri.endswith('/'):
        new_uri = old_uri + 'index.html'
    else:
        new_uri = old_uri
    
    # Log the URI as received by CloudFront and the new URI to be used to fetch from origin
    print(f"Old URI: {old_uri}")
    print(f"New URI: {new_uri}")
    
    # Replace the received URI with the URI that includes the index page
    request['uri'] = new_uri
    
    # Return to CloudFront
    return request
"""),
            description="Lambda@Edge function to rewrite URLs for MkDocs",
            function_name="mkdocs-bucket-edge-function",
        )

        # provide the Lambda function with permissions to read from the S3 bucket
        bucket.grant_read(rewrite_function)

        cfn_origin_access_control = cloudfront.CfnOriginAccessControl(self, "CfnOriginAccessControl",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="mkdocsOAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="description"
            )
        )

        # Update CloudFront distribution
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(    
                origin=origins.S3BucketOrigin(bucket, origin_access_control_id=cfn_origin_access_control.ref),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress=True,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                edge_lambdas=[
                    cloudfront.EdgeLambda(
                        event_type=cloudfront.LambdaEdgeEventType.ORIGIN_REQUEST,
                        function_version=cast(IVersion, rewrite_function.current_version),
                    )
                ]
            ),
            default_root_object=index_page.value_as_string,
            http_version=cloudfront.HttpVersion.HTTP2,
            enabled=True,
        )

        # Add bucket policy to allow CloudFront OAC access
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[cast(IPrincipal, iam.ServicePrincipal("cloudfront.amazonaws.com"))],
                actions=["s3:GetObject"],
                resources=[f"{bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                    }
                }
            )
        )


        # Outputs
        CfnOutput(
            self,
            "BucketNameOutput",
            value=bucket.bucket_name,
            description="Name of the S3 bucket"
        )
        
        CfnOutput(
            self,
            "DistributionId",
            value=distribution.distribution_id,
            description="CloudFront Distribution ID"
        )
        
        CfnOutput(
            self,
            "DistributionDomainName",
            value=distribution.distribution_domain_name,
            description="CloudFront Distribution Domain Name"
        )