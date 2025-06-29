from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    # aws_sqs as sqs,
)
from constructs import Construct

class MkdocsS3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        account_id = self.account
        region = self.region
        s3.Bucket(
            self, 
            id="mkdocs-s3-bucket", 
            bucket_name=f"mkdocs-s3-bucket-{account_id}-{region}",
        )